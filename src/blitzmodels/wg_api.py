from typing import (
    Any,
    Optional,
    ClassVar,
    TypeVar,
    Sequence,
    Tuple,
    Set,
    Self,
    Type,
    Dict,
    Annotated,
)
from types import TracebackType
import logging
import pyarrow  # type: ignore
from bson import ObjectId
from pydantic import (
    field_validator,
    model_validator,
    ConfigDict,
    BaseModel,
    field_serializer,
    Field,
)
from pathlib import Path
from importlib.resources.abc import Traversable
from importlib.resources import as_file
import importlib

from aiohttp import ClientTimeout
from urllib.parse import quote
from collections import defaultdict

# from sortedcollections import SortedDict  # type: ignore
from argparse import ArgumentParser
from configparser import ConfigParser
from pydantic_exportables import (
    JSONExportable,
    PyObjectId,
    TypeExcludeDict,
    Idx,
    IndexSortOrder,
    BackendIndex,
    DESCENDING,
    ASCENDING,
    TEXT,
)
from pydantic_exportables.utils import get_model
from pyutils.utils import epoch_now
from pyutils import ThrottledClientSession

from .region import Region
from .tank import (
    Tank,
    EnumNation,
    EnumVehicleTypeStr,
    EnumVehicleTier,
)
from .types import AccountId, TankId


TYPE_CHECKING = True
logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug

B = TypeVar("B", bound="BaseModel")

_NULL_OBJECT_ID: ObjectId = ObjectId("0" * 24)


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

    model_config = ConfigDict(
        frozen=False, validate_assignment=True, populate_by_name=True
    )

    def str(self) -> str:
        return f"code: {self.code} {self.message}"


class WGTankStatAll(JSONExportable):
    # fmt: off
    battles:            int = Field(default=0, alias="b")
    wins:               int = Field(default=0, alias="w")
    losses:             int = Field(default=0, alias="l")
    capture_points:     int = Field(default=0, alias="cp")
    dropped_capture_points: int = Field(default=0, alias="dp")
    damage_dealt:       int = Field(default=0, alias="dd")
    damage_received:    int = Field(default=0, alias="dr")
    hits:               int = Field(default=0, alias="h")
    frags:              int = Field(default=0, alias="k")
    frags8p:            int | None = None
    max_frags:          int = Field(default=0, alias="mk")
    max_xp:             int | None = None
    shots:              int = Field(default=0, alias="sh")
    spotted:            int = Field(default=0, alias="sp")
    xp:                 int | None = Field(default=0, alias="xp")
    win_and_survived:   int = Field(default=0, alias="ws")
    survived_battles:   int = Field(default=0, alias="sb")
    # fmt: on

    model_config = ConfigDict(
        frozen=False, validate_assignment=True, populate_by_name=True
    )

    # @field_validator("frags8p", "xp", "max_xp")
    # @classmethod
    # def unset(cls, v: int | bool | None) -> None:
    #     return None


# def lateinit_object_id() -> ObjectId:
#     """Required for initializing a model w/o a '_id' field"""
#     raise RuntimeError("lateinit_object_id(): should never be called")


class AccountInfoStats(WGTankStatAll):
    max_frags_tank_id: int = Field(default=0, alias="mft")
    max_xp_tank_id: int = Field(default=0, alias="mxt")


class TankStat(JSONExportable):
    # fmt: off
    id:                 Annotated[PyObjectId, Field(default=_NULL_OBJECT_ID, alias="_id")]
    region:             Region | None = Field(default=None, alias="r")
    all:                WGTankStatAll = Field(..., alias="s")
    last_battle_time:   int = Field(..., alias="lb")
    account_id:         AccountId = Field(..., alias="a")
    tank_id:            TankId = Field(..., alias="t")
    mark_of_mastery:    int = Field(default=0, alias="m")
    battle_life_time:   int = Field(default=0, alias="l")
    release:            str | None = Field(default=None, alias="u")
    max_xp:             int | None = None
    in_garage_updated:  int | None = None
    max_frags:          int | None = None
    frags:              int | None = None
    in_garage:          bool | None = None

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
    # Example TankStat()
    _example: ClassVar[str] = """{
                                "r": "eu",
                                "s": {
                                    "b": 92,
                                    "w": 55,
                                    "l": 37,
                                    "sp": 110,
                                    "h": 606,
                                    "k": 83,
                                    "cp": 6,
                                    "dd": 113782,
                                    "dr": 75358,
                                    "mk": 4,
                                    "sh": 700,
                                    "ws": 35,
                                    "sb": 36,
                                    "dp": 42
                                },
                                "lb": 1621494665,
                                "a": 521458531,
                                "t": 2625,
                                "m": 3,
                                "l": 14401,
                                "u": "7.9"
                                }"""
    # fmt: on
    model_config = ConfigDict(
        # arbitrary_types_allowed=True,
        frozen=False,
        validate_assignment=True,
        populate_by_name=True,
    )

    @field_serializer("id", when_used="json")
    def serialize_ObjectId(self, id: ObjectId, _info) -> str:
        return str(id)

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
    def backend_indexes(cls) -> list[list[tuple[str, IndexSortOrder]]]:
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
        cls, account_id: AccountId, last_battle_time: int, tank_id: TankId = 0
    ) -> ObjectId:
        return ObjectId(
            hex(account_id)[2:].zfill(10)
            + hex(tank_id)[2:].zfill(6)
            + hex(last_battle_time)[2:].zfill(8)
        )

    @field_validator("last_battle_time", mode="before")
    @classmethod
    def validate_lbt(cls, v: int) -> int:
        now: int = epoch_now()
        if v > now + 36000:
            return now
        else:
            return v

    @model_validator(mode="after")
    def set_id_region(self) -> Self:
        try:
            # debug('starting')
            # debug(f'{values}')
            if self.id == _NULL_OBJECT_ID:
                self._set_skip_validation(
                    "id",
                    self.mk_id(self.account_id, self.last_battle_time, self.tank_id),
                )
            if self.region is None:
                self._set_skip_validation("region", Region.from_id(self.account_id))
            return self
        except Exception as err:
            raise ValueError(f"Could not store _id: {err}")

    @field_validator("max_frags", "frags", "max_xp", "in_garage", "in_garage_updated")
    @classmethod
    def unset(cls, v: int | bool | None) -> None:
        return None

    def __str__(self) -> str:
        return f"account_id={self.account_id}:{self.region} \
                    tank_id={self.tank_id} \
                    last_battle_time={self.last_battle_time}"


###########################################
#
# AccountInfo()
#
###########################################


class AccountInfo(JSONExportable):
    # fmt: off
    account_id:         int = Field(alias="id")
    region:             Region | None = Field(default=None, alias="r")
    created_at:         int = Field(default=0, alias="c")
    updated_at:         int = Field(default=0, alias="u")
    nickname:           str | None = Field(default=None, alias="n")
    last_battle_time:   int = Field(default=0, alias="l")
    statistics:         Optional[Dict[str, Optional[AccountInfoStats]]] = Field(default=None, alias="s")
    # fmt: on

    model_config = ConfigDict(
        # arbitrary_types_allowed=True,  # should this be removed?
        frozen=False,
        validate_assignment=True,
        populate_by_name=True,
        extra="allow",
    )

    @model_validator(mode="after")
    def set_region(self) -> Self:
        if self.region is None:
            self._set_skip_validation("region", Region.from_id(self.account_id))
        return self

    _example = """
                {
                "statistics": {
                    "clan": {
                        "spotted": 0,
                        "max_frags_tank_id": 0,
                        "hits": 0,
                        "frags": 0,
                        "max_xp": 0,
                        "max_xp_tank_id": 0,
                        "wins": 0,
                        "losses": 0,
                        "capture_points": 0,
                        "battles": 0,
                        "damage_dealt": 0,
                        "damage_received": 0,
                        "max_frags": 0,
                        "shots": 0,
                        "frags8p": 0,
                        "xp": 0,
                        "win_and_survived": 0,
                        "survived_battles": 0,
                        "dropped_capture_points": 0
                    },
                    "all": {
                        "spotted": 43706,
                        "max_frags_tank_id": 19025,
                        "hits": 269922,
                        "frags": 42016,
                        "max_xp": 2628,
                        "max_xp_tank_id": 6145,
                        "wins": 23280,
                        "losses": 15830,
                        "capture_points": 14713,
                        "battles": 39495,
                        "damage_dealt": 66326446,
                        "damage_received": 43773129,
                        "max_frags": 7,
                        "shots": 319045,
                        "frags8p": 28114,
                        "xp": 35144185,
                        "win_and_survived": 17499,
                        "survived_battles": 18157,
                        "dropped_capture_points": 33297
                    },
                    "frags": null
                },
                "account_id": 521458531,
                "created_at": 1407265587,
                "updated_at": 1704554148,
                "private": null,
                "last_battle_time": 1704553843,
                "nickname": "jylpah"
            }"""


class WGApiWoTBlitz(JSONExportable):
    # fmt: off
    status: str = Field(default="ok", alias="s")
    meta:   Optional[Dict[str, Any]] = Field(default=None, alias="m")
    error:  WGApiError | None = Field(default=None, alias="e")

    _exclude_defaults   : ClassVar[bool] = False
    _exclude_none       : ClassVar[bool] = True
    _exclude_unset      : ClassVar[bool] = False
    # fmt: on

    model_config = ConfigDict(
        frozen=False, validate_assignment=True, populate_by_name=True
    )

    @field_validator("error")
    @classmethod
    def if_error(cls, v: WGApiError | None) -> WGApiError | None:
        if v is not None:
            debug(v.str())
        return v

    def status_error(self) -> None:
        self.status = "error"

    def status_ok(self) -> None:
        self.status = "ok"

    @property
    def is_ok(self):
        return self.status == "ok"


class WGApiWoTBlitzAccountInfo(WGApiWoTBlitz):
    """Model for WG API /wotb/account/info/"""

    data: Dict[str, Optional[AccountInfo]] | None = Field(default=None, alias="d")
    model_config = ConfigDict(
        frozen=False, validate_assignment=True, populate_by_name=True
    )

    def __len__(self) -> int:
        res: int = 0
        if self.data is not None:
            for v in self.data.values():
                if v is not None:
                    res += 1
        return res


class WGApiWoTBlitzTankStats(WGApiWoTBlitz):
    """Model for WG API /wotb/tanks/stats/"""

    data: Dict[str, Optional[list[TankStat]]] | None = Field(default=None, alias="d")

    model_config = ConfigDict(
        frozen=False, validate_assignment=True, populate_by_name=True
    )

    def __len__(self) -> int:
        if self.data is not None:
            for v in self.data.values():
                if v is not None:
                    return len(v)
                break
        return 0


class PlayerAchievements(JSONExportable):
    """Placeholder class for data.achievements that are not collected"""

    model_config = ConfigDict(
        frozen=False, validate_assignment=True, populate_by_name=True, extra="allow"
    )


class PlayerAchievementsMaxSeries(JSONExportable):
    # fmt: off
    id          : Annotated[PyObjectId, Field(default=_NULL_OBJECT_ID, alias="_id")]
    jointVictory: int = Field(default=0, alias="jv")
    account_id  : int = Field(default=0, alias="a")
    region      : Region | None = Field(default=None, alias="r")
    release     : str | None = Field(default=None, alias="u")
    added       : int = Field(default=epoch_now(), alias="t")

    _include_export_DB_fields : ClassVar[Optional[TypeExcludeDict]] = {
        "id": True,
        "jointVictory": True,
        "account_id": True,
        "region": True,
        "release": True,
        "added": True,
    }

    _exclude_defaults : ClassVar[bool] = False

    _example : ClassVar[str] = """{
                "jv": 5825,
                "a": 521458531,
                "r": "eu",
                "u": "10.2",
                "t": 1692296001
                }"""
    # fmt: on
    model_config = ConfigDict(
        frozen=False,
        validate_assignment=True,
        populate_by_name=True,
        # arbitrary_types_allowed=True,
        extra="allow",  # TODO or 'ignore'?
    )

    @field_serializer("id", when_used="json")
    def serialize_ObjectId(self, obj_id: ObjectId, _info) -> str:
        return str(obj_id)

    @property
    def index(self) -> Idx:
        """return backend index"""
        if self.id == _NULL_OBJECT_ID:
            self._set_skip_validation(
                "id",
                self.mk_index(self.account_id, self.region, self.added),
            )
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
    def backend_indexes(cls) -> list[list[tuple[str, IndexSortOrder]]]:
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

    @model_validator(mode="after")
    def set_region_id(self) -> Self:
        if self.region is None and self.account_id > 0:
            self._set_skip_validation("region", Region.from_id(self.account_id))

        self._set_skip_validation(
            "id", self.mk_index(self.account_id, self.region, self.added)
        )
        return self

    def __str__(self) -> str:
        return f"account_id={self.account_id}:{self.region} added={self.added}"

    @classmethod
    def transform_PlayerAchievementsMain(
        cls, in_obj: "PlayerAchievementsMain"
    ) -> Optional["PlayerAchievementsMaxSeries"]:
        """Transform PlayerAchievementsMain object to PlayerAchievementsMaxSeries"""
        try:
            if in_obj.max_series is None:
                raise ValueError(f"in_obj doesn't have 'max_series' set: {in_obj}")
            ms = in_obj.max_series

            if in_obj.account_id is None:
                raise ValueError(f"in_obj doesn't have 'account_id' set: {in_obj}")
            ms.account_id = in_obj.account_id

            if in_obj.updated is None:
                ms.added = epoch_now()
            else:
                ms.added = in_obj.updated

            return ms

        except Exception as err:
            error(f"{err}")
        return None


class PlayerAchievementsMain(JSONExportable):
    achievements: PlayerAchievements | None = Field(default=None, alias="a")
    max_series: PlayerAchievementsMaxSeries | None = Field(default=None, alias="m")
    account_id: int | None = Field(default=None)
    updated: int | None = Field(default=None)

    model_config = ConfigDict(
        frozen=False, validate_assignment=True, populate_by_name=True
    )


PlayerAchievementsMaxSeries.register_transformation(
    PlayerAchievementsMain,
    PlayerAchievementsMaxSeries.transform_PlayerAchievementsMain,
)


class WGApiWoTBlitzPlayerAchievements(WGApiWoTBlitz):
    data: dict[str, PlayerAchievementsMain] | None = Field(default=None, alias="d")

    model_config = ConfigDict(
        frozen=False, validate_assignment=True, populate_by_name=True
    )

    ## CHECK / FIX: This might not work with v2

    @field_validator("data", mode="before")
    @classmethod
    def validate_data(
        cls, v: dict[str, PlayerAchievementsMain | None] | None
    ) -> dict[str, PlayerAchievementsMain] | None:
        if not isinstance(v, dict):
            return None
        else:
            res: dict[str, PlayerAchievementsMain]
            res = {key: value for key, value in v.items() if value is not None}
            return res

    def __len__(self) -> int:
        if self.data is not None:
            return len(self.data)
        return 0

    def get_max_series(self) -> list[PlayerAchievementsMaxSeries]:
        res: list[PlayerAchievementsMaxSeries] = list()
        try:
            if self.data is None:
                return res
            for key, pam in self.data.items():
                try:
                    if pam is None or pam.max_series is None:
                        continue
                    ms: PlayerAchievementsMaxSeries = pam.max_series
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


class WGApiWoTBlitzTankopedia(WGApiWoTBlitz):
    # data should be sorted by integer value of the key = tank_id
    data: Dict[str, Tank] = Field(default=dict(), alias="d")
    codes: Dict[str, Tank] = Field(default=dict(), alias="c")

    _tier_cache: Dict[int, Set[TankId]] = dict()

    _exclude_export_DB_fields = {"codes": True}
    _exclude_export_src_fields = {"codes": True}

    model_config = ConfigDict(
        frozen=False, validate_assignment=True, populate_by_name=True
    )

    @model_validator(mode="after")
    def _validate_code(self) -> Self:
        if len(self.codes) == 0:
            self._set_skip_validation("codes", self._update_codes(data=self.data))
        if len(self._tier_cache) == 0:
            self._set_skip_validation("_tier_cache", self._update_tier_cache())
        return self

    @classmethod
    def default_path(cls) -> Path:
        """
        Return Path of the Tankopedia shipped with the package
        """
        packaged_tankopedia: Traversable = importlib.resources.files(
            "blitzmodels"
        ).joinpath("tanks.json")  # REFACTOR in Python 3.12
        with as_file(packaged_tankopedia) as tankopedia_fn:
            return tankopedia_fn

    @classmethod
    def open_default(cls) -> Optional[Self]:
        """
        Open Tankopedia shipped with the package
        """
        with open(cls.default_path(), "r", encoding="utf-8") as file:
            return cls.parse_str(file.read())

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, key: str | TankId) -> Tank:
        if isinstance(key, int):
            key = str(key)
        return self.data[key]

    def __iter__(self):
        """Iterate tanks in WGApiWoTBlitzTankopedia()"""
        return iter([v for _, v in sorted(self.data.items())])

    def update_count(self) -> None:
        if self.meta is None:
            self.meta = dict()
        self.meta["count"] = len(self.data)

    def _update_tier_cache(self) -> Dict[int, Set[TankId]]:
        """Update tier cache and return new cache"""
        res: Dict[int, Set[TankId]] = dict()
        for tier in range(1, 11):
            res[tier] = set()
        for tank in self.data.values():
            res[tank.tier].add(tank.tank_id)
        return res

    def _code_add(self, tank: Tank, codes: dict[str, Tank]) -> bool:
        if tank.code is not None:
            codes[tank.code] = tank
            return True
        return False

    def add(self, tank: Tank) -> None:
        self.data[str(tank.tank_id)] = tank
        self._tier_cache[tank.tier].add(tank.tank_id)
        self._code_add(tank, self.codes)
        self.update_count()

    def pop(self, tank_id: TankId) -> Tank:
        """Raises KeyError if tank_id is not found in self.data"""
        tank: Tank = self.data.pop(str(tank_id))
        self.update_count()
        if tank.code is not None:
            try:
                del self.codes[tank.code]
                self._tier_cache[tank.tier].remove(tank.tank_id)
            except Exception as err:
                debug(f"could not remove code for tank_id={tank.tank_id}: {err}")
                pass
        return tank

    def by_code(self, code: str) -> Tank | None:
        """Return tank by short code"""
        try:
            return self.codes[code]
        except KeyError as err:
            debug(f"no tank with short code: {code}: {err}")
        return None

    @property
    def has_codes(self):
        """Whether tankopedia has short codes dict"""
        return len(self.codes) > 0

    # @classmethod
    def _update_codes(self, data: dict[str, Tank]) -> dict[str, Tank]:
        """Helper to update .codes"""
        codes: dict[str, Tank] = self.codes.copy()
        for tank in data.values():
            self._code_add(tank, codes)
        return codes

    def update_codes(self) -> None:
        """update _code dict"""
        self._set_skip_validation("codes", self._update_codes(self.data))

    def update_tanks(
        self, new: "WGApiWoTBlitzTankopedia"
    ) -> Tuple[set[TankId], set[TankId]]:
        """update tankopedia with another one"""
        new_ids: set[TankId] = {tank.tank_id for tank in new}
        old_ids: set[TankId] = {tank.tank_id for tank in self}
        added: set[TankId] = new_ids - old_ids
        updated: set[TankId] = new_ids & old_ids
        updated = {tank_id for tank_id in updated if new[tank_id] != self[tank_id]}

        self.data.update({(str(tank_id), new[tank_id]) for tank_id in added})
        updated_ids: set[TankId] = set()
        for tank_id in updated:
            if self.data[str(tank_id)].update(new[tank_id]):
                updated_ids.add(tank_id)
        self.update_count()
        self.update_codes()
        return (added, updated_ids)

    def get_tank_ids_by_tier(self, tier: int) -> Set[TankId]:
        if tier < 1 or tier > 10:
            raise ValueError(f"tier must be between 1-10: {tier}")
        return self._tier_cache[tier]


class WGApiTankString(JSONExportable):
    id: int
    name: str
    nation: EnumNation
    type: EnumVehicleTypeStr = Field(alias="type_slug")
    tier: EnumVehicleTier = Field(alias="level")
    user_string: str
    image_url: str
    preview_image_url: str
    is_premium: bool
    is_collectible: bool

    _url: ClassVar[str] = ".wotblitz.com/en/api/tankopedia/vehicle/"

    model_config = ConfigDict(
        frozen=False, validate_assignment=True, populate_by_name=True
    )

    @field_validator("nation", mode="before")
    @classmethod
    def validate_nation(cls, value) -> int:
        if isinstance(value, str):
            return EnumNation(value).value  # type: ignore
        return value

    @classmethod
    def url(cls, user_string: str, region: Region = Region.eu) -> str:
        """Get URL as string for a 'user_string'"""
        debug("_url: %s", cls._url)
        return f"https://{region}{cls._url}{user_string}/"

    def as_WGTank(self) -> Tank | None:
        try:
            return Tank(
                tank_id=self.id,
                name=self.user_string,
                nation=self.nation,
                type=self.type,
                tier=self.tier,
                is_premium=self.is_premium,
            )
        except Exception as err:
            debug(f"could not transform WGApiTankString to Tank: {self.name}: {err}")
        return None


Tank.register_transformation(WGApiTankString, WGApiTankString.as_WGTank)


class WoTBlitzTankString(JSONExportable):
    code: str = Field(default=..., alias="_id")
    name: str = Field(default=..., alias="n")

    model_config = ConfigDict(
        frozen=False, validate_assignment=True, populate_by_name=True
    )

    @property
    def index(self) -> Idx:
        return self.code

    @property
    def indexes(self) -> dict[str, Idx]:
        """return backend indexes"""
        return {"code": self.index}

    @classmethod
    def backend_indexes(cls) -> list[list[tuple[str, IndexSortOrder]]]:
        indexes: list[list[tuple[str, IndexSortOrder]]] = list()
        indexes.append([("code", TEXT)])
        return indexes


class WGApi:
    # constants
    DEFAULT_WG_APP_ID: str = "81381d3f45fa4aa75b78a7198eb216ad"
    # DEFAULT_LESTA_APP_ID: str = ""

    URL_SERVER = {
        "eu": "https://api.wotblitz.eu/wotb/",
        # "ru": "https://api.wotblitz.ru/wotb/",
        "ru": None,
        "com": "https://api.wotblitz.com/wotb/",
        "asia": "https://api.wotblitz.asia/wotb/",
        "china": None,
    }

    def __init__(
        self,
        app_id: str = DEFAULT_WG_APP_ID,
        # ru_app_id: str = DEFAULT_LESTA_APP_ID,
        # tankopedia_fn : str = 'tanks.json',
        # maps_fn 		: str = 'maps.json',
        rate_limit: float = 10,
        # ru_rate_limit: float = -1,
        default_region: Region = Region.eu,
    ):
        assert app_id is not None, "WG App ID must not be None"
        assert rate_limit is not None, "rate_limit must not be None"
        debug(f"rate_limit: {rate_limit}")
        self.app_id: str = app_id
        # self.ru_app_id: str = ru_app_id
        self.session: dict[str, ThrottledClientSession] = dict()
        self.default_region: Region = default_region

        # if ru_rate_limit < 0:
        #     ru_rate_limit = rate_limit

        headers = {"Accept-Encoding": "gzip, deflate"}

        for region in [Region.eu, Region.com, Region.asia]:
            timeout = ClientTimeout(total=10)
            self.session[region.value] = ThrottledClientSession(
                rate_limit=rate_limit, headers=headers, timeout=timeout
            )
        # for region in [Region.ru]:
        #     timeout = ClientTimeout(total=10)
        #     self.session[region.value] = ThrottledClientSession(
        #         rate_limit=ru_rate_limit, headers=headers, timeout=timeout
        #     )
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
        for server, session in self.session.items():
            try:
                debug(f"trying to close session to {server} server")
                await session.close()
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
    def get_server_url(cls, region: Region = Region.eu) -> str | None:
        assert isinstance(region, Region), "region must be type of Region"
        try:
            return cls.URL_SERVER[region.value]
        except Exception as err:
            error(f"Unknown region: {region.value}")
            debug(str(err))
        return None

    ###########################################
    #
    # get_tank_stats()
    #
    ###########################################

    def get_tank_stats_url(
        self,
        account_id: int,
        region: Region | None = None,
        tank_ids: list[int] = [],
        fields: list[str] = [],
    ) -> Tuple[str, Region] | None:
        # assert isinstance(account_id, int), "account_id must be int"
        # assert isinstance(tank_ids, list), "tank_ids must be a list"
        # assert isinstance(fields, list), "fields must be a list"
        try:
            URL_WG_TANK_STATS: str = "tanks/stats/"

            if region is None:
                region = Region.from_id(account_id)

            server: str | None = self.get_server_url(region)
            if server is None:
                raise ValueError(f"No API server for region {region.value}")

            tank_id_str: str = ""
            if len(tank_ids) > 0:
                tank_id_str = "&tank_id=" + quote(",".join([str(x) for x in tank_ids]))

            field_str: str = ""
            if len(fields) > 0:
                field_str = "&fields=" + quote(",".join(fields))
            # if region == Region.ru:
            #     return (
            #         f"{server}{URL_WG_TANK_STATS}?application_id={self.ru_app_id}&account_id={account_id}{tank_id_str}{field_str}",
            #         account_region,
            #     )
            # else:
            return (
                f"{server}{URL_WG_TANK_STATS}?application_id={self.app_id}&account_id={account_id}{tank_id_str}{field_str}",
                region,
            )
        except Exception as err:
            debug(f"Failed to form url for account_id: {account_id}: {err}")
        return None

    async def get_tank_stats_full(
        self,
        account_id: int,
        region: Region | None = None,
        tank_ids: list[int] = [],
        fields: list[str] = [],
    ) -> WGApiWoTBlitzTankStats | None:
        # assert isinstance(region, Region), "region must be type of Region"
        try:
            if region is None:
                region = Region.from_id(account_id)
            server_url: Tuple[str, Region] | None = self.get_tank_stats_url(
                account_id=account_id, region=region, tank_ids=tank_ids, fields=fields
            )
            if server_url is None:
                raise ValueError("No tank stats available")
            url: str = server_url[0]
            region = server_url[1]

            return await get_model(
                self.session[region.value], url, resp_model=WGApiWoTBlitzTankStats
            )

        except Exception as err:
            error(f"Failed to fetch tank stats for account_id: {account_id}: {err}")
        return None

    async def get_tank_stats(
        self,
        account_id: int,
        region: Region | None = None,
        tank_ids: list[int] = [],
        fields: list[str] = [],
    ) -> list[TankStat] | None:
        try:
            resp: WGApiWoTBlitzTankStats | None = await self.get_tank_stats_full(
                account_id=account_id, region=region, tank_ids=tank_ids, fields=fields
            )
            if resp is None or resp.data is None:
                verbose(
                    f"could not fetch tank stats for account_id={account_id}:{Region.from_id(account_id)}"
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
            # if region == Region.ru:
            #     return f"{server}{URL_WG_ACCOUNT_INFO}?application_id={self.ru_app_id}&account_id={account_str}{field_str}"
            # else:
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
        assert isinstance(region, Region), "region must be type of Region"
        try:
            url: str | None
            if (
                url := self.get_account_info_url(
                    account_ids=account_ids, region=region, fields=fields
                )
            ) is None:
                raise ValueError("No account info available")
            debug(f"URL: {url}")
            return await get_model(
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
    ) -> list[AccountInfo] | None:
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
        self,
        account_ids: Sequence[int],
        region: Region,
        fields: list[str] = list(),
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
            # if region == Region.ru:
            #     return f"{server}{URL_WG_PLAYER_ACHIEVEMENTS}?application_id={self.ru_app_id}&account_id={account_str}{field_str}"
            # else:
            return f"{server}{URL_WG_PLAYER_ACHIEVEMENTS}?application_id={self.app_id}&account_id={account_str}{field_str}"
        except Exception as err:
            debug(f"Failed to form url: {err}")
        return None

    async def get_player_achievements_full(
        self,
        account_ids: list[int],
        region: Region,
        fields: list[str] = list(),
    ) -> WGApiWoTBlitzPlayerAchievements | None:
        # assert isinstance(region, Region), "region must be type of Region"
        try:
            url: str | None
            if (
                url := self.get_player_achievements_url(
                    account_ids=account_ids, region=region, fields=fields
                )
            ) is None:
                raise ValueError("No player achievements available")
            debug(f"URL: {url}")
            return await get_model(
                self.session[region.value],
                url,
                resp_model=WGApiWoTBlitzPlayerAchievements,
            )

        except Exception as err:
            error(f"Failed to fetch player achievements: {err}")
        return None

    async def get_player_achievements(
        self,
        account_ids: list[int],
        region: Region,
        fields: list[str] = list(),
    ) -> list[PlayerAchievementsMaxSeries] | None:
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
        region: Region | None = None,
        fields: list[str] = ["tank_id", "name", "tier", "type", "nation", "is_premium"],
    ) -> str | None:
        URL_WG_TANKOPEDIA: str = "encyclopedia/vehicles/"
        if region is None:
            region = self.default_region
        assert isinstance(region, Region), "region must be type of Region"
        try:
            debug(f"starting, region={region}")
            server: str | None = self.get_server_url(region)
            if server is None:
                raise ValueError(f"No API server for region {region}")

            field_str: str = ""
            if len(fields) > 0:
                field_str = "fields=" + quote(",".join(fields))
            # if region == Region.ru:
            #     return f"{server}{URL_WG_TANKOPEDIA}?application_id={self.ru_app_id}&{field_str}"
            # else:
            return (
                f"{server}{URL_WG_TANKOPEDIA}?application_id={self.app_id}&{field_str}"
            )
        except Exception as err:
            debug(f"Failed to form url: {err}")
        return None

    async def get_tankopedia(
        self,
        region: Region | None = None,
        fields: list[str] = ["tank_id", "name", "tier", "type", "nation", "is_premium"],
    ) -> WGApiWoTBlitzTankopedia | None:
        try:
            url: str | None
            if region is None:
                region = self.default_region
            if (url := self.get_tankopedia_url(region=region, fields=fields)) is None:
                raise ValueError("No player achievements available")
            debug(f"URL: {url}")
            return await get_model(
                self.session[region.value], url, resp_model=WGApiWoTBlitzTankopedia
            )

        except Exception as err:
            error(f"Failed to fetch player achievements: {err}")
        return None

    ###########################################
    #
    # get_tank_str()
    #
    ###########################################

    async def get_tank_str(
        self,
        user_string: str,
        region: Region | None = None,
    ) -> WGApiTankString | None:
        """Return WGApiTankString() for 'user_string'"""
        debug("starting")
        if region is None:
            region = self.default_region
        assert isinstance(region, Region), "region must be type of Region"
        try:
            url: str = WGApiTankString.url(user_string=user_string, region=region)
            debug(f"URL: {url}")
            return await get_model(
                self.session[region.value], url, resp_model=WGApiTankString
            )
        except Exception as err:
            error(f"Failed to fetch tank info for {user_string}: {err}")
        return None


def add_args_wg(parser: ArgumentParser, config: Optional[ConfigParser] = None) -> bool:
    """Helper to add argparse for WG API"""
    try:
        debug("starting")
        WG_RATE_LIMIT: float = 10
        WG_WORKERS: int = 10
        WG_APP_ID: str = WGApi.DEFAULT_WG_APP_ID
        WG_DEFAULT_REGION: str = Region.eu.name
        # # Lesta / RU
        # LESTA_RATE_LIMIT: float = 10
        # LESTA_WORKERS: int = 10
        # LESTA_APP_ID: str = WGApi.DEFAULT_LESTA_APP_ID
        # # NULL_RESPONSES 	: int 	= 20

        if config is not None and "WG" in config.sections():
            configWG = config["WG"]
            WG_RATE_LIMIT = configWG.getfloat("rate_limit", WG_RATE_LIMIT)
            WG_WORKERS = configWG.getint("api_workers", WG_WORKERS)
            WG_APP_ID = configWG.get("app_id", WG_APP_ID)
            WG_DEFAULT_REGION = configWG.get("default_region", WG_DEFAULT_REGION)

        # if config is not None and "LESTA" in config.sections():
        #     configRU = config["LESTA"]
        #     LESTA_RATE_LIMIT = configRU.getfloat("rate_limit", LESTA_RATE_LIMIT)
        #     LESTA_WORKERS = configRU.getint("api_workers", LESTA_WORKERS)
        #     LESTA_APP_ID = configRU.get("app_id", LESTA_APP_ID)

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

        # parser.add_argument(
        #     "--ru-app-id",
        #     type=str,
        #     default=LESTA_APP_ID,
        #     metavar="APP_ID",
        #     help="Set Lesta (RU) APP ID",
        # )
        # parser.add_argument(
        #     "--ru-rate-limit",
        #     type=float,
        #     default=LESTA_RATE_LIMIT,
        #     metavar="RATE_LIMIT",
        #     help="Rate limit for Lesta (RU) API",
        # )
        return True
    except Exception as err:
        error(f"{err}")
    return False
