from pydantic import Field
from pathlib import Path
from hashlib import md5
from zipfile import ZipFile
from io import BytesIO
import aiofiles

from pyutils import JSONExportable
from .release import Release
from .wg_api import WGApiWoTBlitzTankopedia
from .map import Maps

import logging

# Setup logging
logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug

###########################################
#
# ReplayFile
#
###########################################


class ReplayFileMeta(JSONExportable):
    version: str
    title: str = Field(default="")
    dbid: int
    playerName: str
    battleStartTime: int
    playerVehicleName: str
    mapName: str
    arenaUniqueId: int
    battleDuration: float
    vehicleCompDescriptor: int
    camouflageId: int
    mapId: int
    arenaBonusType: int

    @property
    def release(self) -> Release:
        """Return version as Release()"""
        return Release(release=".".join(self.version.split(".")[0:2]))

    def update_title(self, tankopedia: WGApiWoTBlitzTankopedia, maps: Maps) -> str:
        """Create 'title' based on replay meta"""
        tank_name: str = ""
        map_name: str = ""
        if (
            tank := tankopedia.by_code(self.playerVehicleName)
        ) is not None and tank.name is not None:
            tank_name = tank.name
        else:
            tank_name = self.playerVehicleName

        if self.mapName in maps:
            map_name = maps[self.mapName].name
        else:
            map_name = self.mapName
        return f"{tank_name} @ {map_name} by {self.playerName}"


class ReplayFile:
    """Class for reading WoT Blitz replay files"""

    def __init__(self, replay: bytes | Path | str):
        self._path: Path | None = None
        self._data: bytes
        self._hash: str
        self._opened: bool = False
        self.meta: ReplayFileMeta

        if isinstance(replay, str):
            self._path = Path(replay)
        elif isinstance(replay, Path):
            self._path = replay
        elif isinstance(replay, bytes):
            self._data = replay
            self._calc_hash()
            self._opened = True
        else:
            raise TypeError(f"replay is not str, Path or bytes: {type(replay)}")

        if not (self._path is None or self._path.name.lower().endswith(".wotbreplay")):
            raise ValueError(f"file does not have '.wotbreplay' suffix: {self._path}")
        # if not is_zipfile(path):
        #     raise ValueError(f"replay {path} is not a valid Zip file")

    def _calc_hash(self) -> str:
        hash = md5()
        try:
            hash.update(self._data)
        except Exception as err:
            error(f"{err}")
            raise
        self._hash = hash.hexdigest()
        return self._hash

    async def open(self):
        """Open replay"""
        if self._opened or self._path is None:
            error(f"replay has been opened already: replay_id={self._hash}")
            return None
        debug("opening replay: %s", str(self._path))
        async with aiofiles.open(self._path, "rb") as replay:
            self._data = await replay.read()
            self._calc_hash()

        with ZipFile(BytesIO(self._data)) as zreplay:
            with zreplay.open("meta.json") as meta_json:
                self.meta = ReplayFileMeta.model_validate_json(meta_json.read())
        self._opened = True

    @property
    def is_opened(self) -> bool:
        return self._opened

    @property
    def hash(self) -> str:
        if self.is_opened:
            return self._hash
        raise ValueError("replay has not been opened yet. Use open()")

    @property
    def title(self) -> str:
        if self.is_opened:
            return self.meta.title
        raise ValueError("replay has not been opened yet. Use open()")

    @property
    def data(self) -> bytes:
        if self.is_opened:
            return self._data
        raise ValueError("replay has not been opened yet. Use open()")

    @property
    def path(self) -> Path | None:
        return self._path
