import logging
from typing import Optional, cast, Any, AsyncIterable, Iterable
from aiohttp import ClientResponse, FormData
from pathlib import Path
from aiofiles import open
from asyncio import sleep
from pydantic import Field, Extra
from hashlib import md5
from urllib.parse import urlencode, quote
from base64 import b64encode
from zipfile import BadZipFile, Path as ZipPath, is_zipfile, ZipFile
from io import BytesIO

from pyutils import ThrottledClientSession, JSONExportable, awrap
from pyutils.utils import get_url_model, post_url

from .wg_api import WGApiWoTBlitzTankopedia
from .map import Maps
from .replay import ReplayJSON, ReplayFileMeta, ReplayFile, WoTinspectorAPI

# Setup logging
logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug

SLEEP: float = 1


class WIReplaySummary(JSONExportable):
    id: str = Field(default=..., alias="_id")
    player_name: str
    vehicle_descr: int
    region: str

    class Config:
        allow_population_by_field_name = True
        allow_mutation = True
        validate_assignment = True
        extra = Extra.allow


class WIReplaysData(JSONExportable):
    replays: list[WIReplaySummary]

    class Config:
        allow_population_by_field_name = True
        allow_mutation = True
        validate_assignment = True
        extra = Extra.allow


class WoTInspectorAPIReplays(JSONExportable):
    """WoTinspector.com API to list replays available.
    Preferred over spidering  web page listing"""

    status: str = Field(default="ok")
    data: WIReplaysData
    error: dict[str, Any]

    class Config:
        allow_population_by_field_name = True
        allow_mutation = True
        validate_assignment = True
        extra = Extra.allow


## -----------------------------------------------------------
# Class WoTinspector
#
# replays.wotinspector.com
## -----------------------------------------------------------


class WoTinspector:
    URL_WI: str = "https://replays.wotinspector.com"
    URL_REPLAY_LIST: str = URL_WI + "/en/sort/ut/page/"
    URL_REPLAY_DL: str = URL_WI + "/en/download/"
    URL_REPLAY_VIEW: str = URL_WI + "/en/view/"
    API_REPLAY_LIST: str = "https://api.wotinspector.com/replay/list"
    URL_REPLAY_UL: str = "https://api.wotinspector.com/replay/upload?"
    URL_REPLAY_UL_JSON: str = f"{URL_REPLAY_UL}details=full"

    URL_TANK_DB: str = "https://wotinspector.com/static/armorinspector/tank_db_blitz.js"

    MAX_RETRIES: int = 3
    REPLAY_N = 1
    DEFAULT_RATE_LIMIT = 20 / 3600  # 20 requests / hour

    def __init__(
        self, rate_limit: float = DEFAULT_RATE_LIMIT, auth_token: Optional[str] = None
    ):
        debug(f"rate_limit={rate_limit}, auth_token={auth_token}")
        headers: Optional[dict[str, str]] = None
        if auth_token is not None:
            headers = dict()
            headers["Authorization"] = f"Token {auth_token}"

        self.session = ThrottledClientSession(
            rate_limit=rate_limit,
            filters=[
                self.API_REPLAY_LIST,
                self.URL_REPLAY_UL_JSON,
                self.URL_REPLAY_DL,
                self.URL_REPLAY_LIST,
            ],
            re_filter=False,
            limit_filtered=True,
            headers=headers,
        )

    async def close(self) -> None:
        if self.session is not None:
            debug("Closing aiohttp session")
            await self.session.close()

    def get_url_replay_JSON(self, id: str) -> str:
        return f"{self.URL_REPLAY_UL_JSON}&key={id}"

    async def get_replay(self, replay_id: str) -> ReplayJSON | None:
        try:
            replay: ReplayJSON | None
            replay = await get_url_model(
                self.session,
                self.get_url_replay_JSON(replay_id),
                resp_model=ReplayJSON,
            )
            if replay is None:
                return None
            else:
                return replay
        except Exception as err:
            error(f"Unexpected Exception: {err}")
        return None

    async def post_replay(
        self,
        replay: Path | str | bytes,
        uploaded_by: int = 0,
        tankopedia: WGApiWoTBlitzTankopedia | None = None,
        maps: Maps | None = None,
        fetch_json: bool = False,
        title: str | None = None,
        priv: bool = False,
        # N: int = -1,
    ) -> tuple[str | None, ReplayJSON | None]:
        """
        Post a WoT Blitz replay file to replays.WoTinspector.com

        Returns ID of the replay
        """
        filename: str = ""
        try:
            replay_file: ReplayFile = ReplayFile(replay=replay)
            if isinstance(replay, bytes):
                filename = replay_file.hash + ".wotbreplay"
            else:
                await replay_file.open()
                if replay_file.path is None:
                    raise ValueError("error reading reaply file path")
                filename = replay_file.path.name

            try:
                if tankopedia is not None and maps is not None:
                    replay_file.meta.update_title(tankopedia=tankopedia, maps=maps)
                    debug("updated title=%s", replay_file.meta.title)
                else:
                    debug("no tankopedia and maps give to update replay title")
            except ValueError as err:
                pass

            if title is None:
                title = replay_file.title
            if title == "":
                title = f"{replay_file.meta.playerName}"

            # N = N if N > 0 else self.REPLAY_N
            # self.REPLAY_N += 1

            params = {
                "title": title,
                "private": (1 if priv else 0),
                "uploaded_by": uploaded_by,
                "key": replay_file.hash,
                "filename": filename,
            }
            url: str
            if fetch_json:
                url = self.URL_REPLAY_UL_JSON
            else:
                url = self.URL_REPLAY_UL
            url = f"{url}&" + urlencode(params, quote_via=quote)
            headers = {"Content-type": "application/x-www-form-urlencoded"}
            payload = {"file": b64encode(replay_file.data)}
            # payload = {"file": (filename, b64encode(replay_file.data))}
        except BadZipFile as err:
            error(f"corrupted replay file: {filename}")
            return None, None
        except KeyError as err:
            error(f"Unexpected KeyError: {err}")
            return None, None
        # except Exception as err:
        #     error(f"Thread {N}: Unexpected Exception: {err}")
        #     return None, None
        try:
            if (
                res := await post_url(
                    self.session, url=url, headers=headers, data=payload, retries=1
                )
            ) is not None:
                debug("response from %s: %s", url, res)
                if (api_json := WoTinspectorAPI.parse_str(res)) is None:
                    error(f"Could not parse API response: {api_json}")
                    return None, None
                if (replay_json := ReplayJSON.parse_obj(api_json)) is None:
                    error(f"could not parse the JSON response: {res}")
                    return None, None
                else:
                    return replay_file.hash, replay_json
        except Exception as err:
            error(f"Unexpected Error: {type(err)}: {err}")
            return None, None

        debug(f"Could not post replay: {title}: {res}")
        return None, None

    # async def post_replays(
    #     self, filenames: Iterable[Path] | AsyncIterable[Path], **kwargs
    # ) -> list[str | None]:
    #     """Iterate over replays"""
    #     res: list[str | None] = list()
    #     if isinstance(filenames, Iterable):
    #         async for filename in awrap(filenames):
    #             res.append(await self.post_replay(filename=filename, **kwargs))
    #     else:
    #         async for filename in filenames:
    #             res.append(await self.post_replay(filename=filename, **kwargs))
    #     return res

    async def get_replay_listing(self, page: int = 0) -> ClientResponse:
        url: str = self.get_url_replay_listing(page)
        return cast(
            ClientResponse, await self.session.get(url)
        )  # mypy checks fail with aiohttp _request() return type...

    async def get_replay_ids(self, page: int = 0) -> list[str]:
        """Fetch replay ids from API"""
        debug("starting")
        ids: list[str] = list()
        try:
            url: str = self.get_url_replay_list(page=page)
            resp: WoTInspectorAPIReplays | None
            if (
                resp := await get_url_model(
                    self.session, url=url, resp_model=WoTInspectorAPIReplays
                )
            ) is not None:
                for replay in resp.data.replays:
                    ids.append(replay.id)

        except Exception as err:
            error(f"Failed get replay ids: {err}")
        return ids

    @classmethod
    def get_url_replay_listing(cls, page: int) -> str:
        message("get_url_replay_listing(): DEPRECIATED")
        return f"{cls.URL_REPLAY_LIST}{page}?vt=#filters"

    @classmethod
    def get_url_replay_list(
        cls,
        page: int = 0,
        player: int = 0,
        clan: int = 0,
        tier: int = 0,
        type: int = 0,
        tank_id: int = 0,
        map: int = 0,
        mode: int = 0,
    ) -> str:
        # https://api.wotinspector.com/replay/list\?sort=ut\&player=\&tier=\&type=\&vehicle=\&map=\&mode=0\&clan=\&page=0
        return f"{cls.API_REPLAY_LIST}?sort=ut&page={page}&player={player}&clan={clan}&tier={tier}&type={type}&vehicle={tank_id}&map={map}&mode={mode}"

    @classmethod
    def get_url_replay_view(cls, replay_id):
        return cls.URL_REPLAY_VIEW + replay_id

    # @classmethod
    # def parse_replay_ids(cls, doc: str) -> set[str]:
    # 	"""Get replay ids links from WoTinspector.com replay listing page"""
    # 	replay_ids : set[str] = set()
    # 	try:
    # 		soup = BeautifulSoup(doc, 'lxml')
    # 		links = soup.find_all('a')

    # 		for tag in links:
    # 			link = tag.get('href',None)
    # 			id : str | None = cls.get_replay_id(link)
    # 			if id is not None:
    # 				replay_ids.add(id)
    # 				debug('Adding replay link:' + link)
    # 	except Exception as err:
    # 		error(f'Failed to parse replay links {err}')
    # 	return replay_ids

    @classmethod
    def get_replay_id(cls, url: str) -> str | None:
        if (url is not None) and url.startswith(cls.URL_REPLAY_DL):
            return url.rsplit("/", 1)[-1]
        else:
            return None
