from typing import Any, Optional, ClassVar, TypeVar, Sequence, Tuple, Self, Type
from types import TracebackType
import logging
from sys import path
import pyarrow  # type: ignore
from bson.objectid import ObjectId
from pydantic import BaseModel, Extra, root_validator, validator, Field
from aiohttp import ClientTimeout
from urllib.parse import quote
from collections import defaultdict
from sortedcollections import SortedDict  # type: ignore
from argparse import ArgumentParser
from configparser import ConfigParser
from pyutils import (
    JSONExportable,
    TypeExcludeDict,
    Idx,
    BackendIndexType,
    BackendIndex,
    ThrottledClientSession,
)
from pyutils.utils import epoch_now, get_url_JSON_model
from pyutils.exportable import DESCENDING, ASCENDING, TEXT

# Fix relative imports
from pathlib import Path

path.insert(0, str(Path(__file__).parent.parent.resolve()))

from blitzutils.region import Region
from blitzutils.tank import WGTank

TYPE_CHECKING = True
logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug

B = TypeVar("B", bound="BaseModel")


###########################################
#
# WGApiError()
#
###########################################


class WGApiError(JSONExportable):
    code: int | None
    message: str | None
    field: str | None
    value: str | None

    class Config:
        allow_mutation = True
        validate_assignment = True
        allow_population_by_field_name = True

    def str(self) -> str:
        return f"code: {self.code} {self.message}"


###########################################
#
# WGAccountInfo()
#
###########################################


class WGAccountInfo(JSONExportable):
    account_id: int = Field(alias="id")
    region: Region | None = Field(default=None, alias="r")
    created_at: int = Field(default=0, alias="c")
    updated_at: int = Field(default=0, alias="u")
    nickname: str | None = Field(default=None, alias="n")
    last_battle_time: int = Field(default=0, alias="l")

    # _exclude_export_DB_fields	 = None
    # _exclude_export_src_fields = None
    # _include_export_DB_fields	 = None
    # _include_export_src_fields = None

    class Config:
        arbitrary_types_allowed = True
        allow_mutation = True
        validate_assignment = True
        allow_population_by_field_name = True
        extra = Extra.allow

    @root_validator()
    def set_region(cls, values: dict[str, Any]) -> dict[str, Any]:
        account_id = values.get("account_id")
        region = values.get("region")
        if isinstance(account_id, int) and region is None:
            values["region"] = Region.from_id(account_id)
        return values


class WGTankStatAll(JSONExportable):
    battles: int = Field(..., alias="b")
    wins: int = Field(default=-1, alias="w")
    losses: int = Field(default=-1, alias="l")
    spotted: int = Field(default=-1, alias="sp")
    hits: int = Field(default=-1, alias="h")
    frags: int = Field(default=-1, alias="k")
    max_xp: int | None
    capture_points: int = Field(default=-1, alias="cp")
    damage_dealt: int = Field(default=-1, alias="dd")
    damage_received: int = Field(default=-1, alias="dr")
    max_frags: int = Field(default=-1, alias="mk")
    shots: int = Field(default=-1, alias="sh")
    frags8p: int | None
    xp: int | None
    win_and_survived: int = Field(default=-1, alias="ws")
    survived_battles: int = Field(default=-1, alias="sb")
    dropped_capture_points: int = Field(default=-1, alias="dp")

    class Config:
        allow_mutation = True
        validate_assignment = True
        allow_population_by_field_name = True

    @validator("frags8p", "xp", "max_xp")
    def unset(cls, v: int | bool | None) -> None:
        return None


class WGTankStat(JSONExportable):
    id: ObjectId = Field(alias="_id")
    region: Region | None = Field(default=None, alias="r")
    all: WGTankStatAll = Field(..., alias="s")
    last_battle_time: int = Field(..., alias="lb")
    account_id: int = Field(..., alias="a")
    tank_id: int = Field(..., alias="t")
    mark_of_mastery: int = Field(default=0, alias="m")
    battle_life_time: int = Field(default=0, alias="l")
    release: str | None = Field(default=None, alias="u")
    max_xp: int | None
    in_garage_updated: int | None
    max_frags: int | None
    frags: int | None
    in_garage: bool | None

    _exclude_export_DB_fields: ClassVar[Optional[TypeExcludeDict]] = {
        "max_frags": True,
        "frags": True,
        "max_xp": True,
        "in_garage": True,
        "in_garage_updated": True,
    }
    _exclude_export_src_fields: ClassVar[Optional[TypeExcludeDict]] = {"id": True}
    # _include_export_DB_fields	: ClassVar[Optional[TypeExcludeDict]] = None
    # _include_export_src_fields	: ClassVar[Optional[TypeExcludeDict]] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        allow_mutation = True
        validate_assignment = True
        allow_population_by_field_name = True

    @property
    def index(self) -> Idx:
        """return backend index"""
        return self.id

    @property
    def indexes(self) -> dict[str, Idx]:
        """return backend indexes"""
        return {
            "account_id": self.account_id,
            "last_battle_time": self.last_battle_time,
            "tank_id": self.tank_id,
        }

    @classmethod
    def backend_indexes(cls) -> list[list[tuple[str, BackendIndexType]]]:
        indexes: list[list[BackendIndex]] = list()
        indexes.append(
            [
                ("region", ASCENDING),
                ("account_id", ASCENDING),
                ("tank_id", ASCENDING),
                ("last_battle_time", DESCENDING),
            ]
        )
        indexes.append(
            [
                ("region", ASCENDING),
                ("account_id", ASCENDING),
                ("last_battle_time", DESCENDING),
                ("tank_id", ASCENDING),
            ]
        )
        indexes.append(
            [
                ("region", ASCENDING),
                ("release", DESCENDING),
                ("tank_id", ASCENDING),
                ("account_id", ASCENDING),
            ]
        )
        return indexes

    @classmethod
    def arrow_schema(cls) -> pyarrow.schema:
        return pyarrow.schema(
            [
                ("region", pyarrow.dictionary(pyarrow.uint8(), pyarrow.string())),
                ("last_battle_time", pyarrow.int64()),
                ("account_id", pyarrow.int64()),
                ("tank_id", pyarrow.int32()),
                ("mark_of_mastery", pyarrow.int32()),
                ("battle_life_time", pyarrow.int32()),
                ("release", pyarrow.string()),
                ("all.spotted", pyarrow.int32()),
                ("all.hits", pyarrow.int32()),
                ("all.frags", pyarrow.int32()),
                ("all.wins", pyarrow.int32()),
                ("all.losses", pyarrow.int32()),
                ("all.capture_points", pyarrow.int32()),
                ("all.battles", pyarrow.int32()),
                ("all.damage_dealt", pyarrow.int32()),
                ("all.damage_received", pyarrow.int32()),
                ("all.max_frags", pyarrow.int32()),
                ("all.shots", pyarrow.int32()),
                ("all.win_and_survived", pyarrow.int32()),
                ("all.survived_battles", pyarrow.int32()),
                ("all.dropped_capture_points", pyarrow.int32()),
            ]
        )

    @classmethod
    def mk_id(
        cls, account_id: int, last_battle_time: int, tank_id: int = 0
    ) -> ObjectId:
        return ObjectId(
            hex(account_id)[2:].zfill(10)
            + hex(tank_id)[2:].zfill(6)
            + hex(last_battle_time)[2:].zfill(8)
        )

    @validator("last_battle_time", pre=True)
    def validate_lbt(cls, v: int) -> int:
        now: int = epoch_now()
        if v > now + 36000:
            return now
        else:
            return v

    @root_validator(pre=True)
    def set_id(cls, values: dict[str, Any]) -> dict[str, Any]:
        try:
            # debug('starting')
            # debug(f'{values}')
            if "id" not in values and "_id" not in values:
                if "a" in values:
                    values["_id"] = cls.mk_id(values["a"], values["lb"], values["t"])
                else:
                    values["id"] = cls.mk_id(
                        values["account_id"],
                        values["last_battle_time"],
                        values["tank_id"],
                    )
            return values
        except Exception as err:
            raise ValueError(f"Could not store _id: {err}")

    @root_validator(pre=False)
    def set_region(cls, values: dict[str, Any]) -> dict[str, Any]:
        try:
            if "region" not in values or values["region"] is None:
                values["region"] = Region.from_id(values["account_id"])
            return values
        except Exception as err:
            raise ValueError(f"Could not set region: {err}")

    @validator("max_frags", "frags", "max_xp", "in_garage", "in_garage_updated")
    def unset(cls, v: int | bool | None) -> None:
        return None

    def __str__(self) -> str:
        return f"account_id={self.account_id}:{self.region} \
                    tank_id={self.tank_id} \
                    last_battle_time={self.last_battle_time}"


class WGApiWoTBlitz(JSONExportable):
    status: str = Field(default="ok", alias="s")
    meta: dict[str, Any] | None = Field(default=None, alias="m")
    error: WGApiError | None = Field(default=None, alias="e")

    _exclude_defaults = False
    _exclude_none = True
    _exclude_unset = False

    class Config:
        allow_mutation = True
        validate_assignment = True
        allow_population_by_field_name = True

    @validator("error")
    def if_error(cls, v: WGApiError | None) -> WGApiError | None:
        if v is not None:
            error(v.str())
        return v

    def status_error(self) -> None:
        self.status = "error"

    def status_ok(self) -> None:
        self.status = "ok"

    @property
    def is_ok(self):
        return self.status == "ok"


class WGApiWoTBlitzAccountInfo(WGApiWoTBlitz):
    data: dict[str, WGAccountInfo | None] | None = Field(default=None, alias="d")

    class Config:
        allow_mutation = True
        validate_assignment = True
        allow_population_by_field_name = True


class WGApiWoTBlitzTankStats(WGApiWoTBlitz):
    data: dict[str, list[WGTankStat] | None] | None = Field(default=None, alias="d")

    class Config:
        allow_mutation = True
        validate_assignment = True
        allow_population_by_field_name = True


class WGPlayerAchievements(JSONExportable):
    """Placeholder class for data.achievements that are not collected"""

    class Config:
        allow_mutation = True
        validate_assignment = True
        allow_population_by_field_name = True
        extra = Extra.allow


class WGPlayerAchievementsMaxSeries(JSONExportable):
    id: ObjectId | None = Field(default=None, alias="_id")
    jointVictory: int = Field(default=0, alias="jv")
    account_id: int = Field(default=0, alias="a")
    region: Region | None = Field(default=None, alias="r")
    release: str | None = Field(default=None, alias="u")
    added: int = Field(default=epoch_now(), alias="t")

    _include_export_DB_fields = {
        "id": True,
        "jointVictory": True,
        "account_id": True,
        "region": True,
        "release": True,
        "added": True,
    }

    _exclude_defaults = False

    class Config:
        allow_mutation = True
        validate_assignment = True
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        extra = Extra.allow

    @property
    def index(self) -> Idx:
        """return backend index"""
        if self.id is None:
            return self.mk_index(self.account_id, self.region, self.added)
        else:
            return self.id

    @property
    def indexes(self) -> dict[str, Idx]:
        """return backend indexes"""
        return {
            "account_id": self.account_id,
            "region": str(self.region),
            "added": self.added,
        }

    @classmethod
    def backend_indexes(cls) -> list[list[tuple[str, BackendIndexType]]]:
        indexes: list[list[BackendIndex]] = list()
        indexes.append(
            [("region", ASCENDING), ("account_id", ASCENDING), ("added", DESCENDING)]
        )
        indexes.append(
            [
                ("release", DESCENDING),
                ("region", ASCENDING),
                ("account_id", ASCENDING),
                ("added", DESCENDING),
            ]
        )
        return indexes

    @classmethod
    def mk_index(cls, account_id: int, region: Region | None, added: int) -> ObjectId:
        r: int = 0
        if region is not None:
            r = list(Region).index(region)
        return ObjectId(
            hex(account_id)[2:].zfill(10)
            + hex(r)[2:].zfill(6)
            + hex(added)[2:].zfill(8)
        )

    @root_validator
    def set_region_id(cls, values: dict[str, Any]) -> dict[str, Any]:
        r: int = 0
        region: Region | None = values["region"]
        account_id: int = values["account_id"]

        if region is None and account_id > 0:
            region = Region.from_id(account_id)
        values["region"] = region
        values["id"] = cls.mk_index(account_id, region, values["added"])
        # debug(f"account_id={account_id}, region={region}, added={values['added']}, _id = {values['id']}")
        return values

    def __str__(self) -> str:
        return f"account_id={self.account_id}:{self.region} added={self.added}"

    @classmethod
    def transform_WGPlayerAchievementsMain(
        cls, in_obj: "WGPlayerAchievementsMain"
    ) -> Optional["WGPlayerAchievementsMaxSeries"]:
        """Transform WGPlayerAchievementsMain object to WGPlayerAchievementsMaxSeries"""
        try:
            if in_obj.max_series is None:
                raise ValueError(f"in_obj doesn't have 'max_series' set: {in_obj}")
            ms = in_obj.max_series
            if in_obj.account_id is None:
                raise ValueError(f"in_obj doesn't have 'account_id' set: {in_obj}")
            if in_obj.updated is None:
                ms.added = epoch_now()
            else:
                ms.added = in_obj.updated
            ms.account_id = in_obj.account_id
            return ms

        except Exception as err:
            error(f"{err}")
        return None


class WGPlayerAchievementsMain(JSONExportable):
    achievements: WGPlayerAchievements | None = Field(default=None, alias="a")
    max_series: WGPlayerAchievementsMaxSeries | None = Field(default=None, alias="m")
    account_id: int | None = Field(default=None)
    updated: int | None = Field(default=None)

    class Config:
        allow_mutation = True
        validate_assignment = True
        allow_population_by_field_name = True


WGPlayerAchievementsMaxSeries.register_transformation(
    WGPlayerAchievementsMain,
    WGPlayerAchievementsMaxSeries.transform_WGPlayerAchievementsMain,
)


class WGApiWoTBlitzPlayerAchievements(WGApiWoTBlitz):
    data: dict[str, WGPlayerAchievementsMain] | None = Field(default=None, alias="d")

    class Config:
        allow_mutation = True
        validate_assignment = True
        allow_population_by_field_name = True

    @validator("data", pre=True)
    def validate_data(
        cls, v: dict[str, WGPlayerAchievementsMain | None] | None
    ) -> dict[str, WGPlayerAchievementsMain] | None:
        if not isinstance(v, dict):
            return None
        else:
            res: dict[str, WGPlayerAchievementsMain]
            res = {key: value for key, value in v.items() if value is not None}
            return res

    def get_max_series(self) -> list[WGPlayerAchievementsMaxSeries]:
        res: list[WGPlayerAchievementsMaxSeries] = list()
        try:
            if self.data is None:
                return res
            for key, pam in self.data.items():
                try:
                    if pam is None or pam.max_series is None:
                        continue
                    ms: WGPlayerAchievementsMaxSeries = pam.max_series
                    account_id = int(key)
                    ms.account_id = account_id
                    if ms.region is None:
                        if (region := Region.from_id(account_id)) is not None:
                            ms.region = region
                    res.append(ms)
                except Exception as err:
                    error(f"Unknown error parsing 'max_series': {err}")
        except Exception as err:
            error(f"Error getting 'max_series': {err}")
        return res

    def set_regions(self, region: Region) -> None:
        try:
            if self.data is None:
                return None
            for key, pam in self.data.items():
                try:
                    if pam is None or pam.max_series is None:
                        continue
                    else:
                        pam.max_series.region = region
                        self.data[key].max_series = pam.max_series
                except Exception as err:
                    error(f"Unknown error: {err}")
        except Exception as err:
            error(f"Error getting 'max_series': {err}")
        return None


class WGApiTankopedia(WGApiWoTBlitz):
    data: SortedDict[str, WGTank] = Field(default=SortedDict(int), alias="d")
    # userStr	: dict[str, str] | None = Field(default=None, alias='s')

    _exclude_export_DB_fields = {"userStr": True}

    class Config:
        allow_mutation = True
        validate_assignment = True
        allow_population_by_field_name = True

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, key: str | int) -> WGTank:
        if isinstance(key, int):
            key = str(key)
        return self.data[key]

    def __iter__(self):
        """Iterate tanks in WGApiTankopedia()"""
        return iter(self.data.values())

    def update_count(self) -> None:
        if self.meta is None:
            self.meta = dict()
        self.meta["count"] = len(self.data)

    def add(self, tank: WGTank) -> None:
        self.data[str(tank.tank_id)] = tank
        self.update_count()

    def pop(self, tank_id: int) -> WGTank:
        """Raises KeyError if tank_id is not found in self.data"""
        wgtank: WGTank = self.data.pop(str(tank_id))
        self.update_count()
        return wgtank

    def update(self, new: "WGApiTankopedia") -> Tuple[set[int], set[int]]:
        """update tankopedia with another one"""
        new_ids: set[int] = {tank.tank_id for tank in new}
        old_ids: set[int] = {tank.tank_id for tank in self}
        added: set[int] = new_ids - old_ids
        updated: set[int] = new_ids & old_ids
        updated = {tank_id for tank_id in updated if new[tank_id] != self[tank_id]}

        self.data.update({(str(tank_id), new[tank_id]) for tank_id in added | updated})
        self.update_count()
        return (added, updated)

    @validator("data", pre=False)
    def _validate_data(cls, value) -> SortedDict[str, WGTank]:
        if not isinstance(value, SortedDict):
            return SortedDict(int, **value)


class WoTBlitzTankString(JSONExportable):
    code: str = Field(default=..., alias="_id")
    name: str = Field(default=..., alias="n")

    class Config:
        allow_mutation = True
        validate_assignment = True
        allow_population_by_field_name = True

    @property
    def index(self) -> Idx:
        return self.code

    @property
    def indexes(self) -> dict[str, Idx]:
        """return backend indexes"""
        return {"code": self.index}

    @classmethod
    def backend_indexes(cls) -> list[list[tuple[str, BackendIndexType]]]:
        indexes: list[list[tuple[str, BackendIndexType]]] = list()
        indexes.append([("code", TEXT)])
        return indexes

    # @classmethod
    # def from_tankopedia(cls, tankopedia: WGApiTankopedia) -> list['WoTBlitzTankString'] | None:
    # 	res : list[WoTBlitzTankString] = list()
    # 	try:
    # 		if tankopedia.userStr is not None:
    # 			for k, v in tankopedia.userStr.items():
    # 				res.append(WoTBlitzTankString(code=k, name=v))
    # 			return res
    # 	except Exception as err:
    # 		error(f"Could not read tank strings from Tankopedia: {err}")

    # 	return None


class WGApi:
    # constants
    DEFAULT_WG_APP_ID: str = "81381d3f45fa4aa75b78a7198eb216ad"
    DEFAULT_LESTA_APP_ID: str = ""

    URL_SERVER = {
        "eu": "https://api.wotblitz.eu/wotb/",
        "ru": "https://api.wotblitz.ru/wotb/",
        "com": "https://api.wotblitz.com/wotb/",
        "asia": "https://api.wotblitz.asia/wotb/",
        "china": None,
    }

    def __init__(
        self,
        app_id: str = DEFAULT_WG_APP_ID,
        ru_app_id: str = DEFAULT_LESTA_APP_ID,
        # tankopedia_fn : str = 'tanks.json',
        # maps_fn 		: str = 'maps.json',
        rate_limit: float = 10,
        ru_rate_limit: float = -1,
    ):
        assert app_id is not None, "WG App ID must not be None"
        assert rate_limit is not None, "rate_limit must not be None"
        debug(f"rate_limit: {rate_limit}")
        self.app_id: str = app_id
        self.ru_app_id: str = ru_app_id
        self.session: dict[str, ThrottledClientSession] = dict()

        if ru_rate_limit < 0:
            ru_rate_limit = rate_limit

        headers = {"Accept-Encoding": "gzip, deflate"}

        for region in [Region.eu, Region.com, Region.asia]:
            timeout = ClientTimeout(total=10)
            self.session[region.value] = ThrottledClientSession(
                rate_limit=rate_limit, headers=headers, timeout=timeout
            )
        for region in [Region.ru]:
            timeout = ClientTimeout(total=10)
            self.session[region.value] = ThrottledClientSession(
                rate_limit=ru_rate_limit, headers=headers, timeout=timeout
            )
        debug("WG aiohttp session initiated")

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Close aiohttp sessions"""
        for server in self.session.keys():
            try:
                debug(f"trying to close session to {server} server")
                await self.session[server].close()
                debug(f"session to {server} server closed")
            except Exception as err:
                error(f"{err}")
        return None

    def stats(self) -> dict[str, str] | None:
        """Return dict of stats per server"""
        try:
            totals: defaultdict[str, float] = defaultdict(float)
            stats_dict: dict[str, dict[str, float]] = dict()
            for region in self.session.keys():
                if self.session[region].stats_dict["count"] > 0:
                    stats_dict[region] = self.session[region].stats_dict

            res: dict[str, str] = dict()
            for region in stats_dict:
                res[region] = ThrottledClientSession.print_stats(stats_dict[region])

            if len(stats_dict) > 1:
                for region in stats_dict:
                    for stat in stats_dict[region]:
                        totals[stat] += stats_dict[region][stat]
                res["Total"] = ThrottledClientSession.print_stats(totals)
            return res
        except Exception as err:
            error(f"{err}")
        return None

    def print(self) -> None:
        """Print server stats"""
        try:
            stats: dict[str, str] | None = self.stats()
            if stats is not None:
                message("WG API stats:")
                for server in stats:
                    message(f"{server.capitalize():7s}: {stats[server]}")
        except Exception as err:
            error(f"{err}")

    @classmethod
    def get_server_url(cls, region: Region) -> str | None:
        assert region is not None, "region must not be None"
        try:
            return cls.URL_SERVER[region.value]
        except Exception as err:
            error(f"Unknown region: {region.value}")
        return None

    ###########################################
    #
    # get_tank_stats()
    #
    ###########################################

    def get_tank_stats_url(
        self,
        account_id: int,
        region: Region,
        tank_ids: list[int] = [],
        fields: list[str] = [],
    ) -> Tuple[str, Region] | None:
        assert type(account_id) is int, "account_id must be int"
        assert type(tank_ids) is list, "tank_ids must be a list"
        assert type(fields) is list, "fields must be a list"
        assert type(region) is Region, "region must be type of Region"
        try:
            URL_WG_TANK_STATS: str = "tanks/stats/"

            account_region: Region | None = Region.from_id(account_id)

            if account_region is None:
                raise ValueError("Could not determine region for account_id")
            if account_region != region:
                raise ValueError(
                    f"account_id {account_id} does not match region {region.name}"
                )

            server: str | None = self.get_server_url(account_region)
            if server is None:
                raise ValueError(f"No API server for region {account_region.value}")

            tank_id_str: str = ""
            if len(tank_ids) > 0:
                tank_id_str = "&tank_id=" + quote(",".join([str(x) for x in tank_ids]))

            field_str: str = ""
            if len(fields) > 0:
                field_str = "&fields=" + quote(",".join(fields))
            if region == Region.ru:
                return (
                    f"{server}{URL_WG_TANK_STATS}?application_id={self.ru_app_id}&account_id={account_id}{tank_id_str}{field_str}",
                    account_region,
                )
            else:
                return (
                    f"{server}{URL_WG_TANK_STATS}?application_id={self.app_id}&account_id={account_id}{tank_id_str}{field_str}",
                    account_region,
                )
        except Exception as err:
            debug(f"Failed to form url for account_id: {account_id}: {err}")
        return None

    async def get_tank_stats_full(
        self,
        account_id: int,
        region: Region,
        tank_ids: list[int] = [],
        fields: list[str] = [],
    ) -> WGApiWoTBlitzTankStats | None:
        try:
            server_url: Tuple[str, Region] | None = self.get_tank_stats_url(
                account_id=account_id, region=region, tank_ids=tank_ids, fields=fields
            )
            if server_url is None:
                raise ValueError(f"No tank stats available")
            url: str = server_url[0]
            region = server_url[1]

            return await get_url_JSON_model(
                self.session[region.value], url, resp_model=WGApiWoTBlitzTankStats
            )

        except Exception as err:
            error(f"Failed to fetch tank stats for account_id: {account_id}: {err}")
        return None

    async def get_tank_stats(
        self,
        account_id: int,
        region: Region,
        tank_ids: list[int] = [],
        fields: list[str] = [],
    ) -> list[WGTankStat] | None:
        try:
            resp: WGApiWoTBlitzTankStats | None = await self.get_tank_stats_full(
                account_id=account_id, region=region, tank_ids=tank_ids, fields=fields
            )
            if resp is None or resp.data is None:
                verbose(
                    f"could not fetch tank stats for account_id={account_id}:{region}"
                )
                return None
            else:
                return list(resp.data.values())[0]
        except Exception as err:
            debug(f"Failed to fetch tank stats for account_id: {account_id}: {err}")
        return None

    ###########################################
    #
    # get_account_info()
    #
    ###########################################

    def get_account_info_url(
        self,
        account_ids: Sequence[int],
        region: Region,
        fields: list[str] = [
            "account_id",
            "created_at",
            "updated_at",
            "last_battle_time",
            "nickname",
        ],
    ) -> str | None:
        """get URL for /wotb/account/info/"""
        URL_WG_ACCOUNT_INFO: str = "account/info/"
        try:
            debug(f"starting, account_ids={account_ids}, region={region}")
            server: str | None
            if (server := self.get_server_url(region)) is None:
                raise ValueError(f"No API server for region {region}")
            if len(account_ids) == 0:
                raise ValueError("Empty account_id list given")

            account_str: str = quote(",".join([str(a) for a in account_ids]))
            field_str: str = ""
            if len(fields) > 0:
                field_str = "&fields=" + quote(",".join(fields))
            if region == Region.ru:
                return f"{server}{URL_WG_ACCOUNT_INFO}?application_id={self.ru_app_id}&account_id={account_str}{field_str}"
            else:
                return f"{server}{URL_WG_ACCOUNT_INFO}?application_id={self.app_id}&account_id={account_str}{field_str}"
        except Exception as err:
            debug(f"Failed to form url: {err}")
        return None

    async def get_account_info_full(
        self,
        account_ids: Sequence[int],
        region: Region,
        fields: list[str] = [
            "account_id",
            "created_at",
            "updated_at",
            "last_battle_time",
            "nickname",
        ],
    ) -> WGApiWoTBlitzAccountInfo | None:
        """get WG API response for account/info"""
        try:
            url: str | None
            if (
                url := self.get_account_info_url(
                    account_ids=account_ids, region=region, fields=fields
                )
            ) is None:
                raise ValueError(f"No account info available")
            debug(f"URL: {url}")
            return await get_url_JSON_model(
                self.session[region.value], url, resp_model=WGApiWoTBlitzAccountInfo
            )

        except Exception as err:
            error(f"Failed to fetch account info: {err}")
        return None

    async def get_account_info(
        self,
        account_ids: Sequence[int],
        region: Region,
        fields: list[str] = [
            "account_id",
            "created_at",
            "updated_at",
            "last_battle_time",
            "nickname",
        ],
    ) -> list[WGAccountInfo] | None:
        try:
            resp: WGApiWoTBlitzAccountInfo | None
            resp = await self.get_account_info_full(
                account_ids=account_ids, region=region, fields=fields
            )
            if resp is None or resp.data is None:
                error("No stats found")
                return None
            else:
                return [info for info in resp.data.values() if info is not None]
        except Exception as err:
            error(f"Failed to fetch player achievements: {err}")
        return None

    ###########################################
    #
    # get_player_achievements()
    #
    ###########################################

    def get_player_achievements_url(
        self, account_ids: Sequence[int], region: Region, fields: list[str] = list()
    ) -> str | None:
        URL_WG_PLAYER_ACHIEVEMENTS: str = "account/achievements/"
        try:
            debug(f"starting, account_ids={account_ids}, region={region}")
            server: str | None = self.get_server_url(region)
            if server is None:
                raise ValueError(f"No API server for region {region}")
            if len(account_ids) == 0:
                raise ValueError("Empty account_id list given")

            account_str: str = quote(",".join([str(a) for a in account_ids]))
            field_str: str = ""
            if len(fields) > 0:
                field_str = "&fields=" + quote(",".join(fields))
            if region == Region.ru:
                return f"{server}{URL_WG_PLAYER_ACHIEVEMENTS}?application_id={self.ru_app_id}&account_id={account_str}{field_str}"
            else:
                return f"{server}{URL_WG_PLAYER_ACHIEVEMENTS}?application_id={self.app_id}&account_id={account_str}{field_str}"
        except Exception as err:
            debug(f"Failed to form url: {err}")
        return None

    async def get_player_achievements_full(
        self, account_ids: list[int], region: Region, fields: list[str] = list()
    ) -> WGApiWoTBlitzPlayerAchievements | None:
        try:
            url: str | None
            if (
                url := self.get_player_achievements_url(
                    account_ids=account_ids, region=region, fields=fields
                )
            ) is None:
                raise ValueError(f"No player achievements available")
            debug(f"URL: {url}")
            return await get_url_JSON_model(
                self.session[region.value],
                url,
                resp_model=WGApiWoTBlitzPlayerAchievements,
            )

        except Exception as err:
            error(f"Failed to fetch player achievements: {err}")
        return None

    async def get_player_achievements(
        self, account_ids: list[int], region: Region, fields: list[str] = list()
    ) -> list[WGPlayerAchievementsMaxSeries] | None:
        try:
            resp: WGApiWoTBlitzPlayerAchievements | None
            resp = await self.get_player_achievements_full(
                account_ids=account_ids, region=region, fields=fields
            )
            if resp is None or resp.data is None:
                error("No stats found")
                return None
            else:
                resp.set_regions(region)
                return resp.get_max_series()
        except Exception as err:
            error(f"Failed to fetch player achievements: {err}")
        return None

    ###########################################
    #
    # get_tankopedia()
    #
    ###########################################

    def get_tankopedia_url(
        self,
        region: Region,
        fields: list[str] = ["tank_id", "name", "tier", "type", "nation", "is_premium"],
    ) -> str | None:
        URL_WG_TANKOPEDIA: str = "encyclopedia/vehicles/"
        try:
            debug(f"starting, region={region}")
            server: str | None = self.get_server_url(region)
            if server is None:
                raise ValueError(f"No API server for region {region}")

            field_str: str = ""
            if len(fields) > 0:
                field_str = "fields=" + quote(",".join(fields))
            if region == Region.ru:
                return f"{server}{URL_WG_TANKOPEDIA}?application_id={self.ru_app_id}&{field_str}"
            else:
                return f"{server}{URL_WG_TANKOPEDIA}?application_id={self.app_id}&{field_str}"
        except Exception as err:
            debug(f"Failed to form url: {err}")
        return None

    async def get_tankopedia(
        self,
        region: Region,
        fields: list[str] = ["tank_id", "name", "tier", "type", "nation", "is_premium"],
    ) -> WGApiTankopedia | None:
        try:
            url: str | None
            if (url := self.get_tankopedia_url(region=region, fields=fields)) is None:
                raise ValueError(f"No player achievements available")
            debug(f"URL: {url}")
            return await get_url_JSON_model(
                self.session[region.value], url, resp_model=WGApiTankopedia
            )

        except Exception as err:
            error(f"Failed to fetch player achievements: {err}")
        return None


def add_args_wg(parser: ArgumentParser, config: Optional[ConfigParser] = None) -> bool:
    """Helper to add argparse for WG API"""
    try:
        debug("starting")
        WG_RATE_LIMIT: float = 10
        WG_WORKERS: int = 10
        WG_APP_ID: str = WGApi.DEFAULT_WG_APP_ID
        WG_DEFAULT_REGION: str = Region.eu.name
        # Lesta / RU
        LESTA_RATE_LIMIT: float = 10
        LESTA_WORKERS: int = 10
        LESTA_APP_ID: str = WGApi.DEFAULT_LESTA_APP_ID
        # NULL_RESPONSES 	: int 	= 20

        if config is not None and "WG" in config.sections():
            configWG = config["WG"]
            WG_RATE_LIMIT = configWG.getfloat("rate_limit", WG_RATE_LIMIT)
            WG_WORKERS = configWG.getint("api_workers", WG_WORKERS)
            WG_APP_ID = configWG.get("app_id", WG_APP_ID)
            WG_DEFAULT_REGION = configWG.get("default_region", WG_DEFAULT_REGION)

        if config is not None and "LESTA" in config.sections():
            configRU = config["LESTA"]
            LESTA_RATE_LIMIT = configRU.getfloat("rate_limit", LESTA_RATE_LIMIT)
            LESTA_WORKERS = configRU.getint("api_workers", LESTA_WORKERS)
            LESTA_APP_ID = configRU.get("app_id", LESTA_APP_ID)

        parser.add_argument(
            "--wg-workers",
            dest="wg_workers",
            type=int,
            default=WG_WORKERS,
            metavar="WORKERS",
            help="number of async workers",
        )
        parser.add_argument(
            "--wg-app-id",
            type=str,
            default=WG_APP_ID,
            metavar="APP_ID",
            help="Set WG APP ID",
        )
        parser.add_argument(
            "--wg-rate-limit",
            type=float,
            default=WG_RATE_LIMIT,
            metavar="RATE_LIMIT",
            help="rate limit for WG API per server",
        )
        parser.add_argument(
            "--wg-region",
            type=str,
            nargs=1,
            choices=[r.value for r in Region.API_regions()],
            default=WG_DEFAULT_REGION,
            help=f"default API region (default: {WG_DEFAULT_REGION})",
        )

        parser.add_argument(
            "--ru-app-id",
            type=str,
            default=LESTA_APP_ID,
            metavar="APP_ID",
            help="Set Lesta (RU) APP ID",
        )
        parser.add_argument(
            "--ru-rate-limit",
            type=float,
            default=LESTA_RATE_LIMIT,
            metavar="RATE_LIMIT",
            help="Rate limit for Lesta (RU) API",
        )
        return True
    except Exception as err:
        error(f"{err}")
    return False
