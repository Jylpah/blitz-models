"""blitzutils.replay

Classes related WoT Blitz replay JSON files and WoTinspector replay JSON format
"""

from datetime import datetime
from typing import Any, ClassVar, Self, Tuple
from enum import IntEnum, StrEnum
from collections import defaultdict
import logging
from bson.objectid import ObjectId
from pydantic import (
    field_validator,
    model_validator,
    ConfigDict,
    root_validator,
    Field,
    HttpUrl,
)
from pathlib import Path
from hashlib import md5
from zipfile import BadZipFile, Path as ZipPath, is_zipfile, ZipFile
from io import BytesIO

import aiofiles

from pyutils import JSONExportable, Idx, BackendIndexType
from pyutils.exportable import DESCENDING, ASCENDING, TEXT

from .tank import EnumVehicleTypeInt
from .release import Release
from .wg_api import WGApiWoTBlitzTankopedia
from .map import Maps, Map
from .region import Region

logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug


class EnumWinnerTeam(IntEnum):
    # fmt: off
    draw = 0
    one = 1
    two = 2
    # fmt: on


class EnumBattleResult(IntEnum):
    # fmt: off
    incomplete  = -1
    not_win     = 0
    win         = 1
    loss        = 2  # EXPERIMENTAL: not in replays, might be dropped later
    draw        = 3  # EXPERIMENTAL: not in replays, might be dropped later
    # fmt: on

    def __str__(self) -> str:
        return f"{self.name}".capitalize()


class WoTBlitzMaps(StrEnum):
    # fmt: off
    Random      = "Random map"
    amigosville = "Falls Creek"
    asia        = "Lost Temple"
    canal       = "Canal"
    canyon      = "Canyon"
    desert_train = "Desert Sands"
    erlenberg   = "Middleburg"
    faust       = "Faust"
    fort        = "Macragge"
    grossberg   = "Dynasty's Pearl"
    himmelsdorf = "Himmelsdorf"
    italy       = "Vineyards"
    karelia     = "Rockfield"
    karieri     = "Copperfield"
    lake        = "Mirage"
    lumber      = "Alpenstadt"
    malinovka   = "Winter Malinovka"
    medvedkovo  = "Dead Rail"
    milbase     = "Yamato Harbor"
    mountain    = "Black Goldville"
    north       = "North"
    ordeal      = "Trial by Fire"
    pliego      = "Castilla"
    port        = "Port Bay"
    rock        = "Mayan Ruins"
    rudniki     = "Mines"
    savanna     = "Oasis Palms"
    skit        = "Naval Frontier"
    test        = "World of Ducks"
    tutorial    = "Proving Grounds"
    # fmt: on


###########################################
#
# Replays
#
###########################################


class ReplayAchievement(JSONExportable):
    t: int
    v: int


###########################################
#
# ReplayDetail()
#
###########################################


class ReplayDetail(JSONExportable):
    # fmt: off
    achievements : list[ReplayAchievement] | None = Field(default=None, alias='a')
    base_capture_points	: int | None = Field(default=None, alias='bc')
    base_defend_points	: int | None = Field(default=None, alias='bd')
    chassis_id			: int | None = Field(default=None, alias='ch')
    clan_tag			: str | None = Field(default=None, alias='ct')
    clanid				: int | None = Field(default=None, alias='ci')
    credits				: int | None = Field(default=None, alias='cr')
    damage_assisted		: int | None = Field(default=None, alias='da')
    damage_assisted_track: int | None = Field(default=None, alias='dat')
    damage_blocked		: int | None = Field(default=None, alias='db')
    damage_made			: int | None = Field(default=None, alias='dm')
    damage_received		: int | None = Field(default=None, alias='dr')
    dbid				: int  		 = Field(default=..., alias='ai')
    death_reason		: int | None = Field(default=None, alias='de')
    distance_travelled	: int | None = Field(default=None, alias='dt')
    enemies_damaged		: int | None = Field(default=None, alias='ed')
    enemies_destroyed	: int | None = Field(default=None, alias='ek')
    enemies_spotted		: int | None = Field(default=None, alias='es')
    exp					: int | None = Field(default=None, alias='ex')
    exp_for_assist		: int | None = Field(default=None, alias='exa')
    exp_for_damage		: int | None = Field(default=None, alias='exd')
    exp_team_bonus		: int | None = Field(default=None, alias='et')
    gun_id				: int | None = Field(default=None, alias='gi')
    hero_bonus_credits	: int | None = Field(default=None, alias='hc')
    hero_bonus_exp		: int | None = Field(default=None, alias='he')
    hitpoints_left		: int | None = Field(default=None, alias='hl')
    hits_bounced		: int | None = Field(default=None, alias='hb')
    hits_pen			: int | None = Field(default=None, alias='hp')
    hits_received		: int | None = Field(default=None, alias='hr')
    hits_splash			: int | None = Field(default=None, alias='hs')
    killed_by			: int | None = Field(default=None, alias='ki')
    shots_hit			: int | None = Field(default=None, alias='sh')
    shots_made			: int | None = Field(default=None, alias='sm')
    shots_pen			: int | None = Field(default=None, alias='sp')
    shots_splash		: int | None = Field(default=None, alias='ss')
    squad_index			: int | None = Field(default=None, alias='sq')
    time_alive			: int | None = Field(default=None, alias='t')
    turret_id			: int | None = Field(default=None, alias='ti')
    vehicle_descr		: int | None = Field(default=None, alias='vi')
    wp_points_earned	: int | None = Field(default=None, alias='we')
    wp_points_stolen	: int | None = Field(default=None, alias='ws')
    # TODO[pydantic]: The following keys were removed: `allow_mutation`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(extra="allow", frozen=False, validate_assignment=True, populate_by_name=True)


###########################################
#
# ReplaySummary()
#
###########################################


class ReplaySummary(JSONExportable):
    _TimestampFormat: str = "%Y-%m-%d %H:%M:%S"
    # fmt: off
    winner_team     : EnumWinnerTeam | None     = Field(default=..., alias="wt")
    battle_result   : EnumBattleResult | None   = Field(default=..., alias="br")
    room_type       : int | None                = Field(default=None, alias="rt")
    battle_type     : int | None                = Field(default=None, alias="bt")
    uploaded_by     : int                       = Field(default=0, alias="ul")
    title           : str | None                = Field(default=..., alias="t")
    player_name     : str                       = Field(default=..., alias="pn")
    protagonist     : int                       = Field(default=..., alias="p")
    protagonist_team: int | None                = Field(default=..., alias="pt")
    map_name        : str                       = Field(default=..., alias="mn")
    vehicle         : str                       = Field(default=..., alias="v")
    vehicle_tier    : int | None                = Field(default=..., alias="vx")
    vehicle_type    : EnumVehicleTypeInt | None = Field(default=..., alias="vt")
    credits_total   : int | None                = Field(default=None, alias="ct")
    credits_base    : int | None                = Field(default=None, alias="cb")
    exp_base        : int | None                = Field(default=None, alias="eb")
    exp_total       : int | None                = Field(default=None, alias="et")
    battle_start_timestamp: int                 = Field(default=..., alias="bts")
    battle_start_time: str | None               = Field(default=None, repr=False)  # duplicate of 'bts'
    battle_duration : float                     = Field(default=..., alias="bd")
    description     : str | None                = Field(default=None, alias="de")
    arena_unique_id : int                       = Field(default=..., alias="aid")
    allies          : list[int]                 = Field(default=..., alias="a")
    enemies         : list[int]                 = Field(default=..., alias="e")
    mastery_badge   : int | None                = Field(default=None, alias="mb")
    details         : ReplayDetail | list[ReplayDetail] = Field(default=..., alias="d")

    # fmt: on

    model_config = ConfigDict(
        extra="allow", frozen=False, validate_assignment=True, populate_by_name=True
    )

    @field_validator("vehicle_tier")
    @classmethod
    def check_tier(cls, v: int | None) -> int | None:
        if v is not None:
            if v > 10 or v < 0:
                raise ValueError("Tier has to be within [1, 10]")
        return v

    @field_validator("protagonist_team")
    @classmethod
    def check_protagonist_team(cls, v: int) -> int | None:
        if v is None:
            return None
        elif v == 0 or v == 1 or v == 2:
            return v
        else:
            raise ValueError("protagonist_team has to be 0, 1, 2 or None")

    @field_validator("battle_start_time")
    @classmethod
    def return_none(cls, v: str) -> None:
        return None

    @model_validator(mode="after")
    def root(self) -> Self:
        if self.battle_start_time is None:
            self._set_skip_validation(
                "battle_start_time",
                datetime.fromtimestamp(self.battle_start_timestamp).strftime(
                    self._TimestampFormat
                ),
            )
        return self

    @property
    def has_full_details(self) -> bool:
        """Whether the replay has full details or is summary version"""
        return isinstance(self.details, list)


###########################################
#
# ReplayData()
#
###########################################


class ReplayData(JSONExportable):
    # fmt: off
    id          : str | None            = Field(default=None, alias="_id")
    view_url    : HttpUrl | None        = Field(default=None, alias="v")
    download_url: HttpUrl | None        = Field(default=None, alias="d")
    summary     : ReplaySummary = Field(default=..., alias="s")
    
    _ViewUrlBase: str = "https://replays.wotinspector.com/en/view/"
    _DLurlBase  : str = "https://replays.wotinspector.com/en/download/"
    # TODO[pydantic]: The following keys were removed: `allow_mutation`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=False, validate_assignment=True, populate_by_name=True)

    _exclude_export_DB_fields = {
        "view_url": True,
        "download_url": True,
        "summary": {"battle_start_time"},
    }

    @property
    def index(self) -> Idx:
        """return backend index"""
        if self.id is not None:
            return self.id
        raise ValueError("id is missing")

    @property
    def indexes(self) -> dict[str, Idx]:
        """return backend indexes"""
        return {"id": self.index}

    @classmethod
    def backend_indexes(cls) -> list[list[tuple[str, BackendIndexType]]]:
        """return backend search indexes"""
        indexes: list[list[tuple[str, BackendIndexType]]] = list()
        indexes.append(
            [
                ("summary.protagonist", ASCENDING),
                ("summary.room_type", ASCENDING),
                ("summary.vehicle_tier", ASCENDING),
                ("summary.battle_start_timestamp", DESCENDING),
            ]
        )
        indexes.append(
            [
                ("summary.room_type", ASCENDING),
                ("summary.vehicle_tier", ASCENDING),
                ("summary.battle_start_timestamp", DESCENDING),
            ]
        )
        return indexes

    @classmethod
    def transform_ReplayJSON(cls, in_obj: "ReplayJSON") -> "ReplayData":
        return in_obj.data

    @model_validator(mode='after')
    def store_id(self) -> Self:
        try:
            # debug("validating: ReplayData()")
            _id: str
            if self.id is not None:
                # debug("data.id found")
                _id = self.id
            elif self.view_url is not None:
                _id = str(self.view_url).split("/")[-1:][0]
            elif self.download_url is not None:
                _id = str(self.download_url).split("/")[-1:][0]            
            else:
                # debug("could not modify id")
                return self  # could not modify 'id'
                # raise ValueError('Replay ID is missing')
            # debug("setting id=%s", _id)
            if self.id is None:
                self._set_skip_validation("id",_id)
            if self.view_url is None:
                self._set_skip_validation("view_url",HttpUrl(_id))
            if self.download_url is None:
                self._set_skip_validation("download_url",HttpUrl(_id))
            return self
        except Exception as err:
            raise ValueError(f"Error reading replay ID: {err}")


###########################################
#
# ReplayJSON()
#
###########################################


class WoTinspectorAPI(JSONExportable):
    status: str = Field(default="ok", alias="s")
    error: dict[str, Any] = Field(default={}, alias="e")
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=False,
        validate_assignment=True,
        populate_by_name=True,
        extra="allow",
    )

    @property
    def is_ok(self) -> bool:
        return self.status == "ok" and len(self.error) == 0

    @property
    def error_msg(self) -> None | str:
        if self.is_ok:
            return None
        else:
            return ", ".join([f"{k}: {v}" for k, v in self.error.items()])


class ReplayJSON(WoTinspectorAPI):
    # fmt: off
    id      : str | None    = Field(default=None, alias="_id")
    data    : ReplayData    = Field(default=..., alias="d")

    # _URL_REPLAY_JSON: str = "https://api.wotinspector.com/replay/upload?details=full&key="

    _exclude_export_src_fields = {"id": True, "data": {"id": True}}
    _exclude_export_DB_fields = {
        "data": {"id": True, 
                 "view_url": True, 
                 "download_url": True, 
                 "summary": {"battle_start_time"}}
    }

    # fmt: on
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=False,
        validate_assignment=True,
        populate_by_name=True,
    )

    # fmt: off
    _example : ClassVar[str] = """
                {
                "status": "ok",
                "data": {
                    "view_url": "https://replays.wotinspector.com/en/view/3b7602a855568b4961d1cd0f1cda8966",
                    "download_url": "https://replays.wotinspector.com/en/download/3b7602a855568b4961d1cd0f1cda8966",
                    "summary": {
                        "winner_team": 1,
                        "uploaded_by": 0,
                        "credits_total": 99183,
                        "exp_base": 1655,
                        "player_name": "jylpah",
                        "title": "6.5k Ace with Type 61. T49 gives lucky player...",
                        "details": [
                            {
                                "damage_assisted_track": 0,
                                "base_capture_points": 0,
                                "wp_points_earned": 0,
                                "time_alive": 48,
                                "chassis_id": 11010,
                                "hits_received": 4,
                                "shots_splash": 0,
                                "gun_id": 11780,
                                "hits_pen": 4,
                                "hero_bonus_credits": 0,
                                "hitpoints_left": 0,
                                "dbid": 536213792,
                                "shots_pen": 0,
                                "exp_for_assist": 0,
                                "damage_received": 1800,
                                "hits_bounced": 0,
                                "hero_bonus_exp": 0,
                                "enemies_damaged": 0,
                                "achievements": [
                                    {
                                        "t": 407,
                                        "v": 0
                                    }
                                ],
                                "exp_for_damage": 0,
                                "damage_blocked": 0,
                                "distance_travelled": 316,
                                "hits_splash": 0,
                                "credits": 9963,
                                "squad_index": null,
                                "wp_points_stolen": 0,
                                "damage_made": 0,
                                "vehicle_descr": 5377,
                                "exp_team_bonus": 348,
                                "clan_tag": "DIDO",
                                "enemies_spotted": 2,
                                "shots_hit": 0,
                                "clanid": 92390,
                                "turret_id": 8963,
                                "enemies_destroyed": 0,
                                "killed_by": 575226685,
                                "base_defend_points": 0,
                                "exp": 410,
                                "damage_assisted": 0,
                                "death_reason": 0,
                                "shots_made": 0
                            },
                            {
                                "damage_assisted_track": 797,
                                "base_capture_points": 0,
                                "wp_points_earned": 0,
                                "time_alive": 213,
                                "chassis_id": 15618,
                                "hits_received": 4,
                                "shots_splash": 0,
                                "gun_id": 17924,
                                "hits_pen": 4,
                                "hero_bonus_credits": 0,
                                "hitpoints_left": 0,
                                "dbid": 559057313,
                                "shots_pen": 3,
                                "exp_for_assist": 34,
                                "damage_received": 1071,
                                "hits_bounced": 0,
                                "hero_bonus_exp": 0,
                                "enemies_damaged": 3,
                                "achievements": [
                                    {
                                        "t": 411,
                                        "v": 1
                                    },
                                    {
                                        "t": 403,
                                        "v": 2
                                    }
                                ],
                                "exp_for_damage": 158,
                                "damage_blocked": 0,
                                "distance_travelled": 524,
                                "hits_splash": 0,
                                "credits": 25531,
                                "squad_index": null,
                                "wp_points_stolen": 0,
                                "damage_made": 1961,
                                "vehicle_descr": 7425,
                                "exp_team_bonus": 159,
                                "clan_tag": "GS1A",
                                "enemies_spotted": 0,
                                "shots_hit": 3,
                                "clanid": 123268,
                                "turret_id": 12547,
                                "enemies_destroyed": 0,
                                "killed_by": 567156835,
                                "base_defend_points": 0,
                                "exp": 375,
                                "damage_assisted": 103,
                                "death_reason": 0,
                                "shots_made": 5
                            },
                            {
                                "damage_assisted_track": 1021,
                                "base_capture_points": 0,
                                "wp_points_earned": 70,
                                "time_alive": 348,
                                "chassis_id": 7010,
                                "hits_received": 8,
                                "shots_splash": 0,
                                "gun_id": 5732,
                                "hits_pen": 7,
                                "hero_bonus_credits": 0,
                                "hitpoints_left": 598,
                                "dbid": 521458531,
                                "shots_pen": 22,
                                "exp_for_assist": 133,
                                "damage_received": 1119,
                                "hits_bounced": 1,
                                "hero_bonus_exp": 0,
                                "enemies_damaged": 7,
                                "achievements": [
                                    {
                                        "t": 473,
                                        "v": 3
                                    },
                                    {
                                        "t": 407,
                                        "v": 1
                                    },
                                    {
                                        "t": 418,
                                        "v": 14
                                    },
                                    {
                                        "t": 451,
                                        "v": 12
                                    },
                                    {
                                        "t": 411,
                                        "v": 17
                                    },
                                    {
                                        "t": 401,
                                        "v": 22
                                    },
                                    {
                                        "t": 403,
                                        "v": 17
                                    },
                                    {
                                        "t": 448,
                                        "v": 2
                                    },
                                    {
                                        "t": 472,
                                        "v": 2
                                    }
                                ],
                                "exp_for_damage": 902,
                                "damage_blocked": 1210,
                                "distance_travelled": 1334,
                                "hits_splash": 0,
                                "credits": 66122,
                                "squad_index": null,
                                "wp_points_stolen": 70,
                                "damage_made": 6540,
                                "vehicle_descr": 3425,
                                "exp_team_bonus": 348,
                                "clan_tag": "AFK",
                                "enemies_spotted": 4,
                                "shots_hit": 23,
                                "clanid": 8606,
                                "turret_id": 6499,
                                "enemies_destroyed": 2,
                                "killed_by": 0,
                                "base_defend_points": 0,
                                "exp": 1655,
                                "damage_assisted": 305,
                                "death_reason": -1,
                                "shots_made": 26
                            },
                            {
                                "damage_assisted_track": 0,
                                "base_capture_points": 0,
                                "wp_points_earned": 0,
                                "time_alive": 326,
                                "chassis_id": 26658,
                                "hits_received": 4,
                                "shots_splash": 0,
                                "gun_id": 17700,
                                "hits_pen": 4,
                                "hero_bonus_credits": 0,
                                "hitpoints_left": 0,
                                "dbid": 528552197,
                                "shots_pen": 4,
                                "exp_for_assist": 33,
                                "damage_received": 1400,
                                "hits_bounced": 0,
                                "hero_bonus_exp": 0,
                                "enemies_damaged": 4,
                                "achievements": [
                                    {
                                        "t": 411,
                                        "v": 0
                                    },
                                    {
                                        "t": 403,
                                        "v": 0
                                    }
                                ],
                                "exp_for_damage": 81,
                                "damage_blocked": 0,
                                "distance_travelled": 428,
                                "hits_splash": 0,
                                "credits": 34581,
                                "squad_index": 1,
                                "wp_points_stolen": 0,
                                "damage_made": 908,
                                "vehicle_descr": 13345,
                                "exp_team_bonus": 167,
                                "clan_tag": "ELITA",
                                "enemies_spotted": 1,
                                "shots_hit": 6,
                                "clanid": 1745,
                                "turret_id": 22819,
                                "enemies_destroyed": 0,
                                "killed_by": 567156835,
                                "base_defend_points": 0,
                                "exp": 343,
                                "damage_assisted": 807,
                                "death_reason": 0,
                                "shots_made": 12
                            },
                            {
                                "damage_assisted_track": 0,
                                "base_capture_points": 0,
                                "wp_points_earned": 0,
                                "time_alive": 159,
                                "chassis_id": 37410,
                                "hits_received": 5,
                                "shots_splash": 0,
                                "gun_id": 26148,
                                "hits_pen": 5,
                                "hero_bonus_credits": 0,
                                "hitpoints_left": 0,
                                "dbid": 558590215,
                                "shots_pen": 1,
                                "exp_for_assist": 69,
                                "damage_received": 1200,
                                "hits_bounced": 0,
                                "hero_bonus_exp": 0,
                                "enemies_damaged": 1,
                                "achievements": [
                                    {
                                        "t": 411,
                                        "v": 0
                                    },
                                    {
                                        "t": 467,
                                        "v": 12
                                    },
                                    {
                                        "t": 403,
                                        "v": 0
                                    }
                                ],
                                "exp_for_damage": 10,
                                "damage_blocked": 400,
                                "distance_travelled": 505,
                                "hits_splash": 0,
                                "credits": 11960,
                                "squad_index": 1,
                                "wp_points_stolen": 0,
                                "damage_made": 0,
                                "vehicle_descr": 18209,
                                "exp_team_bonus": 348,
                                "clan_tag": "JA18",
                                "enemies_spotted": 0,
                                "shots_hit": 2,
                                "clanid": 102012,
                                "turret_id": 32035,
                                "enemies_destroyed": 0,
                                "killed_by": 534757082,
                                "base_defend_points": 0,
                                "exp": 510,
                                "damage_assisted": 909,
                                "death_reason": 0,
                                "shots_made": 5
                            },
                            {
                                "damage_assisted_track": 0,
                                "base_capture_points": 0,
                                "wp_points_earned": 0,
                                "time_alive": 189,
                                "chassis_id": 20002,
                                "hits_received": 12,
                                "shots_splash": 0,
                                "gun_id": 13860,
                                "hits_pen": 7,
                                "hero_bonus_credits": 0,
                                "hitpoints_left": 0,
                                "dbid": 560320179,
                                "shots_pen": 2,
                                "exp_for_assist": 86,
                                "damage_received": 2050,
                                "hits_bounced": 5,
                                "hero_bonus_exp": 0,
                                "enemies_damaged": 2,
                                "achievements": [
                                    {
                                        "t": 411,
                                        "v": 1
                                    },
                                    {
                                        "t": 403,
                                        "v": 1
                                    }
                                ],
                                "exp_for_damage": 41,
                                "damage_blocked": 1597,
                                "distance_travelled": 442,
                                "hits_splash": 0,
                                "credits": 15921,
                                "squad_index": null,
                                "wp_points_stolen": 0,
                                "damage_made": 284,
                                "vehicle_descr": 9505,
                                "exp_team_bonus": 348,
                                "clan_tag": "WARS_",
                                "enemies_spotted": 1,
                                "shots_hit": 4,
                                "clanid": 117952,
                                "turret_id": 16931,
                                "enemies_destroyed": 0,
                                "killed_by": 542645589,
                                "base_defend_points": 0,
                                "exp": 583,
                                "damage_assisted": 1153,
                                "death_reason": 0,
                                "shots_made": 6
                            },
                            {
                                "damage_assisted_track": 742,
                                "base_capture_points": 0,
                                "wp_points_earned": 0,
                                "time_alive": 295,
                                "chassis_id": 15618,
                                "hits_received": 5,
                                "shots_splash": 0,
                                "gun_id": 8452,
                                "hits_pen": 4,
                                "hero_bonus_credits": 0,
                                "hitpoints_left": 0,
                                "dbid": 574043280,
                                "shots_pen": 4,
                                "exp_for_assist": 63,
                                "damage_received": 1010,
                                "hits_bounced": 1,
                                "hero_bonus_exp": 0,
                                "enemies_damaged": 4,
                                "achievements": [
                                    {
                                        "t": 476,
                                        "v": 19
                                    },
                                    {
                                        "t": 411,
                                        "v": 1
                                    },
                                    {
                                        "t": 407,
                                        "v": 0
                                    },
                                    {
                                        "t": 403,
                                        "v": 1
                                    },
                                    {
                                        "t": 409,
                                        "v": 0
                                    }
                                ],
                                "exp_for_damage": 215,
                                "damage_blocked": 225,
                                "distance_travelled": 862,
                                "hits_splash": 0,
                                "credits": 23565,
                                "squad_index": null,
                                "wp_points_stolen": 0,
                                "damage_made": 1229,
                                "vehicle_descr": 7425,
                                "exp_team_bonus": 348,
                                "clan_tag": null,
                                "enemies_spotted": 0,
                                "shots_hit": 4,
                                "clanid": null,
                                "turret_id": 12547,
                                "enemies_destroyed": 1,
                                "killed_by": 542645589,
                                "base_defend_points": 0,
                                "exp": 712,
                                "damage_assisted": 0,
                                "death_reason": 0,
                                "shots_made": 6
                            },
                            {
                                "damage_assisted_track": 0,
                                "base_capture_points": 0,
                                "wp_points_earned": 130,
                                "time_alive": 348,
                                "chassis_id": 40978,
                                "hits_received": 3,
                                "shots_splash": 0,
                                "gun_id": 23572,
                                "hits_pen": 3,
                                "hero_bonus_credits": 0,
                                "hitpoints_left": 158,
                                "dbid": 567156835,
                                "shots_pen": 7,
                                "exp_for_assist": 0,
                                "damage_received": 942,
                                "hits_bounced": 0,
                                "hero_bonus_exp": 0,
                                "enemies_damaged": 6,
                                "achievements": [
                                    {
                                        "t": 407,
                                        "v": 2
                                    },
                                    {
                                        "t": 451,
                                        "v": 23
                                    },
                                    {
                                        "t": 475,
                                        "v": 12
                                    },
                                    {
                                        "t": 409,
                                        "v": 2
                                    },
                                    {
                                        "t": 411,
                                        "v": 5
                                    },
                                    {
                                        "t": 467,
                                        "v": 18
                                    },
                                    {
                                        "t": 401,
                                        "v": 20
                                    },
                                    {
                                        "t": 413,
                                        "v": 4
                                    },
                                    {
                                        "t": 402,
                                        "v": 35
                                    },
                                    {
                                        "t": 403,
                                        "v": 5
                                    },
                                    {
                                        "t": 405,
                                        "v": 0
                                    }
                                ],
                                "exp_for_damage": 535,
                                "damage_blocked": 0,
                                "distance_travelled": 921,
                                "hits_splash": 0,
                                "credits": 30607,
                                "squad_index": 1,
                                "wp_points_stolen": 130,
                                "damage_made": 3136,
                                "vehicle_descr": 16657,
                                "exp_team_bonus": 348,
                                "clan_tag": "UK123",
                                "enemies_spotted": 0,
                                "shots_hit": 8,
                                "clanid": 108540,
                                "turret_id": 34067,
                                "enemies_destroyed": 4,
                                "killed_by": 0,
                                "base_defend_points": 0,
                                "exp": 1021,
                                "damage_assisted": 0,
                                "death_reason": -1,
                                "shots_made": 10
                            },
                            {
                                "damage_assisted_track": 351,
                                "base_capture_points": 0,
                                "wp_points_earned": 40,
                                "time_alive": 343,
                                "chassis_id": 11010,
                                "hits_received": 6,
                                "shots_splash": 0,
                                "gun_id": 3844,
                                "hits_pen": 6,
                                "hero_bonus_credits": 0,
                                "hitpoints_left": 0,
                                "dbid": 542645589,
                                "shots_pen": 5,
                                "exp_for_assist": 19,
                                "damage_received": 1908,
                                "hits_bounced": 0,
                                "hero_bonus_exp": 0,
                                "enemies_damaged": 4,
                                "achievements": [
                                    {
                                        "t": 451,
                                        "v": 7
                                    },
                                    {
                                        "t": 411,
                                        "v": 5
                                    },
                                    {
                                        "t": 403,
                                        "v": 5
                                    }
                                ],
                                "exp_for_damage": 177,
                                "damage_blocked": 640,
                                "distance_travelled": 812,
                                "hits_splash": 0,
                                "credits": 19982,
                                "squad_index": null,
                                "wp_points_stolen": 40,
                                "damage_made": 1420,
                                "vehicle_descr": 5377,
                                "exp_team_bonus": 159,
                                "clan_tag": "EASY2",
                                "enemies_spotted": 0,
                                "shots_hit": 5,
                                "clanid": 73704,
                                "turret_id": 8963,
                                "enemies_destroyed": 2,
                                "killed_by": 567156835,
                                "base_defend_points": 0,
                                "exp": 390,
                                "damage_assisted": 103,
                                "death_reason": 0,
                                "shots_made": 6
                            },
                            {
                                "damage_assisted_track": 0,
                                "base_capture_points": 0,
                                "wp_points_earned": 0,
                                "time_alive": 138,
                                "chassis_id": 8738,
                                "hits_received": 8,
                                "shots_splash": 0,
                                "gun_id": 4388,
                                "hits_pen": 5,
                                "hero_bonus_credits": 0,
                                "hitpoints_left": 0,
                                "dbid": 566298774,
                                "shots_pen": 1,
                                "exp_for_assist": 24,
                                "damage_received": 1850,
                                "hits_bounced": 3,
                                "hero_bonus_exp": 0,
                                "enemies_damaged": 1,
                                "achievements": [
                                    {
                                        "t": 411,
                                        "v": 1
                                    },
                                    {
                                        "t": 403,
                                        "v": 13
                                    }
                                ],
                                "exp_for_damage": 45,
                                "damage_blocked": 880,
                                "distance_travelled": 504,
                                "hits_splash": 0,
                                "credits": 15110,
                                "squad_index": null,
                                "wp_points_stolen": 0,
                                "damage_made": 290,
                                "vehicle_descr": 4385,
                                "exp_team_bonus": 348,
                                "clan_tag": "KANAS",
                                "enemies_spotted": 0,
                                "shots_hit": 2,
                                "clanid": 25664,
                                "turret_id": 8227,
                                "enemies_destroyed": 0,
                                "killed_by": 575226685,
                                "base_defend_points": 0,
                                "exp": 510,
                                "damage_assisted": 305,
                                "death_reason": 0,
                                "shots_made": 2
                            },
                            {
                                "damage_assisted_track": 325,
                                "base_capture_points": 0,
                                "wp_points_earned": 0,
                                "time_alive": 210,
                                "chassis_id": 257058,
                                "hits_received": 10,
                                "shots_splash": 0,
                                "gun_id": 257316,
                                "hits_pen": 7,
                                "hero_bonus_credits": 0,
                                "hitpoints_left": 0,
                                "dbid": 555979223,
                                "shots_pen": 5,
                                "exp_for_assist": 51,
                                "damage_received": 1850,
                                "hits_bounced": 3,
                                "hero_bonus_exp": 0,
                                "enemies_damaged": 3,
                                "achievements": [
                                    {
                                        "t": 411,
                                        "v": 0
                                    },
                                    {
                                        "t": 403,
                                        "v": 0
                                    }
                                ],
                                "exp_for_damage": 97,
                                "damage_blocked": 1870,
                                "distance_travelled": 896,
                                "hits_splash": 0,
                                "credits": 33762,
                                "squad_index": 1,
                                "wp_points_stolen": 0,
                                "damage_made": 1003,
                                "vehicle_descr": 19233,
                                "exp_team_bonus": 159,
                                "clan_tag": "ELITA",
                                "enemies_spotted": 2,
                                "shots_hit": 5,
                                "clanid": 1745,
                                "turret_id": 257059,
                                "enemies_destroyed": 0,
                                "killed_by": 574043280,
                                "base_defend_points": 0,
                                "exp": 357,
                                "damage_assisted": 543,
                                "death_reason": 0,
                                "shots_made": 8
                            },
                            {
                                "damage_assisted_track": 0,
                                "base_capture_points": 0,
                                "wp_points_earned": 0,
                                "time_alive": 240,
                                "chassis_id": 26882,
                                "hits_received": 8,
                                "shots_splash": 0,
                                "gun_id": 23812,
                                "hits_pen": 7,
                                "hero_bonus_credits": 0,
                                "hitpoints_left": -3,
                                "dbid": 534757082,
                                "shots_pen": 4,
                                "exp_for_assist": 21,
                                "damage_received": 2050,
                                "hits_bounced": 1,
                                "hero_bonus_exp": 0,
                                "enemies_damaged": 3,
                                "achievements": [
                                    {
                                        "t": 411,
                                        "v": 1
                                    }
                                ],
                                "exp_for_damage": 150,
                                "damage_blocked": 710,
                                "distance_travelled": 916,
                                "hits_splash": 0,
                                "credits": 18245,
                                "squad_index": null,
                                "wp_points_stolen": 0,
                                "damage_made": 1637,
                                "vehicle_descr": 11521,
                                "exp_team_bonus": 159,
                                "clan_tag": "BGPRO",
                                "enemies_spotted": 1,
                                "shots_hit": 5,
                                "clanid": 77791,
                                "turret_id": 22275,
                                "enemies_destroyed": 1,
                                "killed_by": 521458531,
                                "base_defend_points": 0,
                                "exp": 363,
                                "damage_assisted": 476,
                                "death_reason": 0,
                                "shots_made": 7
                            },
                            {
                                "damage_assisted_track": 0,
                                "base_capture_points": 0,
                                "wp_points_earned": 0,
                                "time_alive": 275,
                                "chassis_id": 1154,
                                "hits_received": 4,
                                "shots_splash": 0,
                                "gun_id": 1412,
                                "hits_pen": 4,
                                "hero_bonus_credits": 0,
                                "hitpoints_left": -3,
                                "dbid": 565503964,
                                "shots_pen": 11,
                                "exp_for_assist": 0,
                                "damage_received": 1400,
                                "hits_bounced": 0,
                                "hero_bonus_exp": 0,
                                "enemies_damaged": 6,
                                "achievements": [
                                    {
                                        "t": 411,
                                        "v": 5
                                    },
                                    {
                                        "t": 403,
                                        "v": 6
                                    }
                                ],
                                "exp_for_damage": 130,
                                "damage_blocked": 350,
                                "distance_travelled": 1266,
                                "hits_splash": 0,
                                "credits": 17868,
                                "squad_index": null,
                                "wp_points_stolen": 0,
                                "damage_made": 1665,
                                "vehicle_descr": 897,
                                "exp_team_bonus": 159,
                                "clan_tag": "STPOW",
                                "enemies_spotted": 2,
                                "shots_hit": 14,
                                "clanid": 122441,
                                "turret_id": 1411,
                                "enemies_destroyed": 0,
                                "killed_by": 521458531,
                                "base_defend_points": 0,
                                "exp": 378,
                                "damage_assisted": 0,
                                "death_reason": 0,
                                "shots_made": 18
                            },
                            {
                                "damage_assisted_track": 0,
                                "base_capture_points": 0,
                                "wp_points_earned": 20,
                                "time_alive": 155,
                                "chassis_id": 19218,
                                "hits_received": 7,
                                "shots_splash": 0,
                                "gun_id": 11540,
                                "hits_pen": 5,
                                "hero_bonus_credits": 0,
                                "hitpoints_left": 0,
                                "dbid": 575226685,
                                "shots_pen": 3,
                                "exp_for_assist": 44,
                                "damage_received": 1800,
                                "hits_bounced": 2,
                                "hero_bonus_exp": 0,
                                "enemies_damaged": 2,
                                "achievements": [
                                    {
                                        "t": 451,
                                        "v": 38
                                    },
                                    {
                                        "t": 409,
                                        "v": 1
                                    }
                                ],
                                "exp_for_damage": 170,
                                "damage_blocked": 1390,
                                "distance_travelled": 521,
                                "hits_splash": 0,
                                "credits": 21619,
                                "squad_index": null,
                                "wp_points_stolen": 20,
                                "damage_made": 1377,
                                "vehicle_descr": 7953,
                                "exp_team_bonus": 159,
                                "clan_tag": "MEAT",
                                "enemies_spotted": 1,
                                "shots_hit": 4,
                                "clanid": 29147,
                                "turret_id": 15123,
                                "enemies_destroyed": 2,
                                "killed_by": 567156835,
                                "base_defend_points": 0,
                                "exp": 399,
                                "damage_assisted": 935,
                                "death_reason": 0,
                                "shots_made": 5
                            }
                        ],
                        "vehicle": "Type 61",
                        "enemies": [
                            528552197,
                            542645589,
                            555979223,
                            559057313,
                            565503964,
                            575226685,
                            534757082
                        ],
                        "description": null,
                        "battle_duration": 371.59491,
                        "arena_unique_id": 17197149452668068,
                        "vehicle_tier": 9,
                        "battle_start_time": "2021-03-08 20:44:23",
                        "mastery_badge": 4,
                        "protagonist": 521458531,
                        "battle_type": 1,
                        "exp_total": 7446,
                        "allies": [
                            521458531,
                            558590215,
                            536213792,
                            574043280,
                            566298774,
                            567156835,
                            560320179
                        ],
                        "vehicle_type": 1,
                        "battle_start_timestamp": 1615236263.0,
                        "credits_base": 66122,
                        "protagonist_team": 1,
                        "map_name": "Castilla",
                        "room_type": 1,
                        "battle_result": 1
                    }
                },
                "error": {}
                }
                """
    # fmt: on

    @property
    def index(self) -> Idx:
        """return backend index"""
        if self.id is not None:
            return self.id
        raise ValueError("id is missing")

    @property
    def indexes(self) -> dict[str, Idx]:
        """return backend indexes"""
        return {"id": self.index}

    def get_id(self) -> str | None:
        try:
            if self.id is not None:
                return self.id
            else:
                return self.data.id
        except Exception as err:
            error(f"Could not read replay id: {err}")
        return None

    @model_validator(mode="after")
    def store_id(self) -> Self:
        # debug("validating: ReplayJSON()")
        if self.id is not None:
            pass
        elif self.data.id is not None:
            # debug("data.id=%s", values["data"].id)
            self._set_skip_validation("id", self.data.id)
        else:
            debug("no 'id' field found")
        # debug("set id=%s", values["id"])
        return self

    # def get_url_json(self) -> str:
    #     return f"{self._URL_REPLAY_JSON}{self.id}"

    def get_enemies(self, player: int | None = None) -> list[int]:
        if player is None or (player in self.data.summary.allies):
            return self.data.summary.enemies
        elif player in self.data.summary.enemies:
            return self.data.summary.allies
        else:
            raise ValueError(f"account_id {player} not found in replay")

    def get_allies(self, player: int | None = None) -> list[int]:
        if player is None or (player in self.data.summary.allies):
            return self.data.summary.allies
        elif player in self.data.summary.enemies:
            return self.data.summary.enemies
        else:
            raise ValueError(f"player {player} not found in replay")

    def get_players(self) -> list[int]:
        return self.get_enemies() + self.get_allies()

    def get_platoons(
        self, player: int | None = None
    ) -> Tuple[defaultdict[int, list[int]], defaultdict[int, list[int]]]:
        if not isinstance(self.data.summary.details, list):
            raise ValueError(
                "replay JSON is summary format: cannot get platoons w/o full details"
            )
        allied_platoons: defaultdict[int, list[int]] = defaultdict(list)
        enemy_platoons: defaultdict[int, list[int]] = defaultdict(list)

        allies = self.get_allies(player)

        for d in self.data.summary.details:
            if d.squad_index is not None and d.squad_index > 0:
                account_id = d.dbid
                if account_id in allies:
                    allied_platoons[d.squad_index].append(account_id)
                else:
                    enemy_platoons[d.squad_index].append(account_id)

        return allied_platoons, enemy_platoons

    def get_battle_result(self, player: int | None = None) -> EnumBattleResult:
        try:
            if self.data.summary.battle_result == EnumBattleResult.incomplete:
                return EnumBattleResult.incomplete

            elif player is not None and player in self.get_enemies():
                if self.data.summary.battle_result == EnumBattleResult.win:
                    return EnumBattleResult.loss
                elif self.data.summary.winner_team == EnumWinnerTeam.draw:
                    return EnumBattleResult.draw
                else:
                    return EnumBattleResult.win

            elif player is None or player in self.get_allies():
                if self.data.summary.battle_result == EnumBattleResult.win:
                    return EnumBattleResult.win
                elif self.data.summary.winner_team == EnumWinnerTeam.draw:
                    return EnumBattleResult.draw
                else:
                    return EnumBattleResult.loss
            else:
                debug(f"player ({str(player)}) not in the battle")
                return EnumBattleResult.incomplete
        except Exception as err:
            raise Exception("Error reading replay")


ReplayData.register_transformation(ReplayJSON, ReplayData.transform_ReplayJSON)


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
        title: str = ""
        if (
            tank := tankopedia.by_code(self.playerVehicleName)
        ) is not None and tank.name is not None:
            title = tank.name
        else:
            raise ValueError("could not find tank name from tankopedia")
        try:
            self.title = f"{title} @ {maps[self.mapName].name}"
            return self.title
        except KeyError as err:
            debug(f"map not found with key: {self.mapName}")
        raise ValueError(f"could not find map for code: {self.mapName}")


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


###########################################
#
# WoTinspector API v2
#
###########################################


###########################################
#
# WIReplay()
#
###########################################


class WIReplay(JSONExportable):
    """Replay schema on https://api.wotinspector.com/"""

    _TimestampFormat: str = "%Y-%m-%d %H:%M:%S"
    # fmt: off
    id              : str                       = Field(default=..., alias="_id") # new
    map_id          : int                       = Field(default=..., alias="mi")  # new
    battle_duration : float                     = Field(default=..., alias="bd")


    winner_team     : EnumWinnerTeam | None     = Field(default=..., alias="wt")
    battle_result   : EnumBattleResult | None   = Field(default=..., alias="br")
    room_type       : int | None                = Field(default=None, alias="rt")
    battle_type     : int | None                = Field(default=None, alias="bt")
    uploaded_by     : int                       = Field(default=0, alias="ul")
    title           : str | None                = Field(default=..., alias="t")
    player_name     : str                       = Field(default=..., alias="pn")
    protagonist     : int                       = Field(default=..., alias="p")
    protagonist_team: int | None                = Field(default=..., alias="pt")
    map_name        : str                       = Field(default=..., alias="mn")
    vehicle         : str                       = Field(default=..., alias="v")
    vehicle_tier    : int | None                = Field(default=..., alias="vx")
    vehicle_type    : EnumVehicleTypeInt | None = Field(default=..., alias="vt")
    credits_total   : int | None                = Field(default=None, alias="ct")
    credits_base    : int | None                = Field(default=None, alias="cb")
    exp_base        : int | None                = Field(default=None, alias="eb")
    exp_total       : int | None                = Field(default=None, alias="et")
    battle_start_timestamp: int                 = Field(default=..., alias="bts")
    battle_start_time: str | None               = Field(default=None, repr=False)  # duplicate of 'bts'
    
    description     : str | None                = Field(default=None, alias="de")
    arena_unique_id : int                       = Field(default=..., alias="aid")
    allies          : list[int]                 = Field(default=..., alias="a")
    enemies         : list[int]                 = Field(default=..., alias="e")
    mastery_badge   : int | None                = Field(default=None, alias="mb")
    details         : ReplayDetail | list[ReplayDetail] = Field(default=..., alias="d")
    # TODO[pydantic]: The following keys were removed: `allow_mutation`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(extra="allow", frozen=False, validate_assignment=True, populate_by_name=True)

    @field_validator("vehicle_tier")
    @classmethod
    def check_tier(cls, v: int | None) -> int | None:
        if v is not None:
            if v > 10 or v < 0:
                raise ValueError("Tier has to be within [1, 10]")
        return v

    @field_validator("protagonist_team")
    @classmethod
    def check_protagonist_team(cls, v: int) -> int | None:
        if v is None:
            return None
        elif v == 0 or v == 1 or v == 2:
            return v
        else:
            raise ValueError("protagonist_team has to be 0, 1, 2 or None")

    @field_validator("battle_start_time")
    @classmethod
    def return_none(cls, v: str) -> None:
        return None


    @model_validator(mode="after")
    def root(self) -> Self:
        if self.battle_start_time is None:
            self._set_skip_validation(
                "battle_start_time",
                datetime.fromtimestamp(self.battle_start_timestamp).strftime(
                    self._TimestampFormat
                ),
            )
        return self


    @property
    def has_full_details(self) -> bool:
        """Whether the replay has full details or is summary version"""
        return isinstance(self.details, list)
