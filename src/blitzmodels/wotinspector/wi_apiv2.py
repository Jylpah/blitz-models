# generated by datamodel-codegen:
#   filename:  WI-API-v2.yaml
#   timestamp: 2023-12-02T17:08:46+00:00

from __future__ import annotations

from enum import Enum, IntEnum
from typing import (
    Any,
    AsyncIterable,
    AsyncIterator,
    ClassVar,
    Mapping,
    Optional,
    Sequence,
    Self,
    Type,
    List,
    Dict,
)
from datetime import datetime
from types import TracebackType
from aiohttp import ClientSession, FormData
from pydantic import (
    AnyUrl,
    AwareDatetime,
    ConfigDict,
    Field,
    FieldSerializationInfo,
    field_validator,
    model_validator,
)
from zipfile import BadZipFile
from pathlib import Path
from urllib.parse import urlencode, quote
from base64 import b64encode

from pyutils import ThrottledClientSession
from pyutils.utils import post_url
from pydantic_exportables import JSONExportable
from pydantic_exportables.utils import get_model


from .wi_apiv1 import ReplayDetail, EnumWinnerTeam, EnumBattleResult

from ..wg_api import WGApiWoTBlitzTankopedia
from ..map import Maps
from ..replay import ReplayFile

import logging

# Setup logging
logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug


class MasteryBadge(IntEnum):
    ace_tanker = 4
    first_class = 3
    second_class = 2
    third_class = 1
    no = 0


class ChatMessage(JSONExportable):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )
    channel: int
    sender: int
    target: int
    time: float
    cmd: int
    message: str


class GameVersion(JSONExportable):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )
    name: str
    package: str
    created_at: AwareDatetime


class MapEntry(JSONExportable):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )
    map_id: int = Field(..., ge=-2147483648, le=2147483647)
    battle_types: str = Field(..., max_length=64)
    access_codes: str = Field(..., max_length=64, pattern="^\\w+(?:,\\w+)*$")


class PaginatedGameVersionList(JSONExportable):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )
    next: Optional[AnyUrl] = Field(
        None, examples=["http://api.example.org/accounts/?page=4"]
    )
    previous: Optional[AnyUrl] = Field(
        None, examples=["http://api.example.org/accounts/?page=2"]
    )
    results: Optional[Sequence[GameVersion]] = None


class PlatformEnum(int, Enum):
    integer_0 = 0
    integer_1 = 1


class PlayerData(JSONExportable):
    """Class for player specific data in replay files. Was ReplayData in version 1"""

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )
    # fmt: off
    # should this be List[Dict[str, int]] instead? 
    achievements        : Sequence[Mapping[str, int]] | None = Field(default=None, alias='a')
    team                : int       = Field(default=-1, alias="t")
    name                : str | None= Field(default=None, alias="n")
    base_capture_points	: int       = Field(default=0, alias='bc')
    base_defend_points	: int       = Field(default=0, alias='bd')
    chassis_id			: int | None= Field(default=None, alias='ch')
    clan_tag            : str | None= Field(default=None, alias='ct')
    clanid              : int | None= Field(default=None, alias='ci')
    credits				: int       = Field(default=0, alias='cr')
    damage_assisted		: int       = Field(default=0, alias='da')
    damage_assisted_track: int      = Field(default=0, alias='dat')
    damage_blocked		: int       = Field(default=0, alias='db')
    damage_made			: int       = Field(default=0, alias='dm')
    damage_received		: int       = Field(default=0, alias='dr')
    dbid				: int  	 = Field(default=..., alias='id')   # is 'ai' in v1 !!
    death_reason		: int | None= Field(default=None, alias='de')
    distance_travelled	: int       = Field(default=0, alias='dt')
    enemies_damaged		: int       = Field(default=0, alias='ed')
    enemies_destroyed	: int       = Field(default=0, alias='ek')
    enemies_spotted		: int       = Field(default=0, alias='es')
    entity_id           : int | None= Field(default=None, alias="ei")
    exp					: int       = Field(default=0, alias='ex')
    exp_for_assist		: int       = Field(default=0, alias='exa')
    exp_for_damage		: int       = Field(default=0, alias='exd')
    exp_team_bonus		: int       = Field(default=0, alias='et')
    gun_id				: int | None= Field(default=None, alias='gi')
    hero_bonus_credits	: int       = Field(default=0, alias='hc')
    hero_bonus_exp		: int       = Field(default=0, alias='he')
    hitpoints_left		: int       = Field(default=0, alias='hl')
    hits_bounced		: int       = Field(default=0, alias='hb')
    hits_pen			: int       = Field(default=0, alias='hp')
    hits_received		: int       = Field(default=0, alias='hr')
    hits_splash			: int       = Field(default=0, alias='hs')
    killed_by			: int | None= Field(default=None, alias='ki')
    shots_made			: int       = Field(default=0, alias='sm')
    shots_hit			: int       = Field(default=0, alias='sh')
    shots_pen			: int       = Field(default=0, alias='sp')
    shots_splash		: int       = Field(default=0, alias='ss')
    squad_index			: int | None= Field(default=None, alias='sq')
    time_alive			: int       = Field(default=-1, alias='ta')  # is 't' in v1 !!!!
    turret_id			: int | None= Field(default=None, alias='ti')
    vehicle_descr		: int       = Field(default=0, alias='vi')
    wp_points_earned	: int       = Field(default=0, alias='we')
    wp_points_stolen	: int       = Field(default=0, alias='ws')
    # fmt: on

    model_config = ConfigDict(
        extra="allow", frozen=False, validate_assignment=True, populate_by_name=True
    )

    @field_validator(
        "vehicle_descr",
        "base_capture_points",
        "base_defend_points",
        "credits",
        "hero_bonus_credits",
        "hero_bonus_exp",
        "exp",
        "exp_for_assist",
        "exp_for_damage",
        "exp_team_bonus",
        "distance_travelled",
        "gun_id",
        "enemies_damaged",
        "enemies_spotted",
        "enemies_destroyed",
        "damage_assisted",
        "damage_assisted_track",
        "damage_blocked",
        "damage_made",
        "damage_received",
        "hitpoints_left",
        "hits_bounced",
        "hits_pen",
        "hits_received",
        "hits_splash",
        "shots_hit",
        "shots_made",
        "shots_pen",
        "shots_splash",
        "wp_points_earned",
        "wp_points_stolen",
        mode="before",
    )
    @classmethod
    def validate_none(cls, value: str | None) -> str:
        if value is None:
            return "0"
        else:
            return value

    @field_validator("team", "time_alive", mode="before")
    @classmethod
    def validate_none_minus1(cls, value: str | None) -> str:
        if value is None:
            return "-1"
        else:
            return value

    _example = """
    {
      "team": 1,
      "name": "jylpah",
      "entity_id": 10361636,
      "dbid": 521458531,
      "clanid": 156,
      "clan_tag": "SPRTA",
      "hitpoints_left": 0,
      "credits": 16277,
      "exp": 592,
      "shots_made": 9,
      "shots_hit": 7,
      "shots_splash": 0,
      "shots_pen": 4,
      "damage_made": 2650,
      "damage_received": 2600,
      "damage_assisted": 549,
      "damage_assisted_track": 450,
      "hits_received": 15,
      "hits_bounced": 4,
      "hits_splash": 0,
      "hits_pen": 11,
      "enemies_spotted": 0,
      "enemies_damaged": 3,
      "enemies_destroyed": 0,
      "time_alive": 224,
      "distance_travelled": 726,
      "killed_by": 10361635,
      "base_capture_points": 0,
      "base_defend_points": 0,
      "exp_for_damage": 208,
      "exp_for_assist": 60,
      "exp_team_bonus": 171,
      "wp_points_earned": 0,
      "wp_points_stolen": 0,
      "hero_bonus_credits": 0,
      "hero_bonus_exp": 0,
      "death_reason": 0,
      "achievements": [
        {
          "t": 411,
          "v": 2
        },
        {
          "t": 403,
          "v": 2
        }
      ],
      "vehicle_descr": 58641,
      "turret_id": 28947,
      "gun_id": 21012,
      "chassis_id": 34834,
      "squad_index": 0,
      "damage_blocked": 4700
    }
    """

    @classmethod
    def from_ReplayDetail(cls, replay_detail: ReplayDetail) -> Self | None:
        """convert V1 ReplayDetail to V2 PlayerData"""
        try:
            d: dict[str, Any] = replay_detail.model_dump()

            # dbid field
            d["id"] = d["ai"]
            del d["ai"]

            # time_alive
            d["ta"] = d["t"]
            del d["t"]

            return cls.model_validate(d)
        except KeyError as err:
            error(f"{err}")
        return None


class Product(JSONExportable):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )
    sku: str = Field(..., description="Item's id (SKU).", max_length=128)
    localization: str


class Replay(JSONExportable):
    """
    Model for a replay
    """

    _TimestampFormat: ClassVar[str] = "%Y-%m-%d %H:%M:%S"

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )
    # fmt: off
    # id: str
    id              : str               = Field(default=..., alias="_id")
    # map_id: int
    map_id          : int               = Field(default=-1, alias="mi")  # not in v1
    # battle_duration: float
    battle_duration : float             = Field(default=..., alias="bd")
    title           : Optional[str]     = Field(default=None, alias="t")
    player_name     : str               = Field(default=..., alias="pn")
    protagonist     : int               = Field(default=..., alias="p")
    vehicle_descr   : int               = Field(default=-1, alias='vi')    # not in v1
    # mastery_badge: int
    mastery_badge   : MasteryBadge      = Field(default=MasteryBadge.no, alias="mb")  # can be None
    # exp_base: int
    exp_base        : int               = Field(default=0, alias="eb")  # can be None
    # enemies_spotted     : int
    enemies_spotted : int               = Field(default=0, alias='es')  # can be None
    # enemies_destroyed   : int
    enemies_destroyed: int               = Field(default=0, alias='ek')  # can be None
    # damage_assisted     : int
    damage_assisted : int               = Field(default=0, alias='da')  # can be None
    # damage_made         : int
    damage_made     : int               = Field(default=0, alias='dm')  # can be None
    # details_url: AnyUrl
    details_url     : AnyUrl | None     = Field(default=None, alias="deu") # ReplayData.view_url in v1
    # download_url: AnyUrl
    download_url    : AnyUrl | None     = Field(default=None, alias="dlu")
    game_version    : Mapping[str, Any] = Field(default_factory=dict, alias="gv")  # not in v1
    arena_unique_id : str               = Field(default=..., alias="aid") # was 'int' in v1
    download_count  : int               = Field(default=0, alias='dlc')    # not in v1
    data_version    : int               = Field(default=-1, alias='ver')    # not in v1
    private         : Optional[bool]    = Field(default=False, alias="priv") # not in v1
    private_clan    : bool              = Field(default=False, alias="pric") # not in v1
    battle_start_time: AwareDatetime    = Field(alias="bts")                # is 'int' in v1 and has 'str' counterpart
    # upload_time: AwareDatetime
    upload_time     : AwareDatetime | None = Field(default=None, alias="uts") # not in v1
    allies          : Sequence[int]     = Field(default_factory=list, alias="a")
    enemies         : Sequence[int]     = Field(default_factory=list, alias="e")
    # protagonist_clan    : int  
    protagonist_clan: int | None        = Field(default=None, alias='pc') # can be None
    # protagonist_team: int
    protagonist_team: int | None        = Field(default=None, alias="pt")
    # battle_result: int
    battle_result   : EnumBattleResult | None = Field(default=..., alias="br")
    # credits_base: int
    credits_base    : int               = Field(default=0, alias="cb")
    tags            : Sequence[int]     = Field(default_factory=list, alias="tgs") # not in v1
    # battle_type   : int
    battle_type     : int | None        = Field(default=None, alias="bt")
    # room_type: int
    room_type       : int | None        = Field(default=None, alias="rt")
    last_accessed_time: AwareDatetime | None = Field(default=None)  # not in v1, not needed
    # winner_team: int
    winner_team     : EnumWinnerTeam | None = Field(default=None, alias="wt")
    finish_reason   : int               = Field(default=-1, alias="ft")  # not in v1, Enum??
    players_data    : Sequence[PlayerData] = Field(default_factory=list, alias="d") # in v1 ReplayDetail | list[ReplayDetail]
    # exp_total: int
    exp_total       : int               = Field(default=0, alias="et")
    # credits_total : int
    credits_total   : int               = Field(default=0, alias="ct")
    # repair_cost: int
    repair_cost     : int               = Field(default=0, alias="rc")
    # exp_free: int
    exp_free        : int               = Field(default=0, alias="ef")
    # exp_free_base: int
    exp_free_base   : int               = Field(default=0, alias="efb")
    # exp_penalty: int
    exp_penalty     : int               = Field(default=0, alias="ep")
    # credits_penalty: int
    credits_penalty : int               = Field(default=0, alias="cp")
    # credits_contribution_in: int
    credits_contribution_in: int         = Field(default=0, alias="cci")
    # credits_contribution_out: int
    credits_contribution_out: int       = Field(default=0, alias="cco")
    camouflage_id   : int               = Field(default=-1, alias="cid")
    # fmt: on

    @field_validator(
        "mastery_badge",
        "exp_base",
        "exp_total",
        "exp_free",
        "exp_free_base",
        "exp_penalty",
        "enemies_spotted",
        "enemies_destroyed",
        "damage_assisted",
        "damage_made",
        "download_count",
        "credits_base",
        "credits_total",
        "credits_penalty",
        "credits_contribution_in",
        "credits_contribution_out",
        "repair_cost",
        mode="before",
    )
    @classmethod
    def validate_none(cls, value: str | None) -> str:
        if value is None:
            return "0"
        else:
            return value

    @field_validator(
        "finish_reason",
        "data_version",
        "camouflage_id",
        "vehicle_descr",
        "map_id",
        mode="before",
    )
    @classmethod
    def validate_none_minus1(cls, value: str | None) -> str:
        if value is None:
            return "-1"
        else:
            return value

    @property
    def is_complete(self) -> bool:
        return self.winner_team is not None

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

    # @property
    # def has_full_details(self) -> bool:
    #     """Whether the replay has full details or is summary version"""
    #     return isinstance(self.player_data, list)

    _example = """
    {
  "id": "4e82956ce42fd8090a70d02a886a18be",
  "map_id": 5,
  "battle_duration": 245.33473,
  "title": "VK 72.01 (K) @ Falls Creek",
  "player_name": "jylpah",
  "protagonist": 521458531,
  "vehicle_descr": 58641,
  "mastery_badge": 0,
  "exp_base": 592,
  "enemies_spotted": 0,
  "enemies_destroyed": 0,
  "damage_assisted": 999,
  "damage_made": 2650,
  "details_url": "https://replays.wotinspector.com/en/view/4e82956ce42fd8090a70d02a886a18be",
  "download_url": "https://replays.wotinspector.com/download/4e82956ce42fd8090a70d02a886a18be",
  "game_version": {
    "name": "10.1.0_apple",
    "package": "blitz10.1"
  },
  "arena_unique_id": "16117927324875930",
  "download_count": 0,
  "data_version": 6,
  "private": false,
  "private_clan": false,
  "battle_start_time": "2023-07-18T20:57:01Z",
  "upload_time": "2023-10-02T05:58:12.711136Z",
  "allies": [
    521458531,
    597563210,
    564799647,
    650763665,
    665370740,
    594896096,
    538458467
  ],
  "enemies": [
    588636999,
    596090909,
    542046639,
    612849634,
    581974895,
    597219828,
    520032043
  ],
  "protagonist_clan": 500000156,
  "protagonist_team": 1,
  "battle_result": 0,
  "credits_base": 16277,
  "tags": [
    0
  ],
  "battle_type": 1,
  "room_type": 1,
  "last_accessed_time": "2023-10-02T13:22:23.552216Z",
  "winner_team": 2,
  "finish_reason": 1,
  "players_data": [
      {
      "team": 1,
      "name": "Apex_LGN",
      "entity_id": 10361638,
      "dbid": 650763665,
      "clanid": 210033,
      "clan_tag": "_TQT_",
      "hitpoints_left": 0,
      "credits": 10144,
      "exp": 594,
      "shots_made": 8,
      "shots_hit": 7,
      "shots_splash": 0,
      "shots_pen": 5,
      "damage_made": 2287,
      "damage_received": 1900,
      "damage_assisted": 262,
      "damage_assisted_track": 0,
      "hits_received": 8,
      "hits_bounced": 2,
      "hits_splash": 0,
      "hits_pen": 6,
      "enemies_spotted": 2,
      "enemies_damaged": 3,
      "enemies_destroyed": 1,
      "time_alive": 171,
      "distance_travelled": 640,
      "killed_by": 10361631,
      "base_capture_points": 0,
      "base_defend_points": 0,
      "exp_for_damage": 193,
      "exp_for_assist": 19,
      "exp_team_bonus": 180,
      "wp_points_earned": 365,
      "wp_points_stolen": 0,
      "hero_bonus_credits": 0,
      "hero_bonus_exp": 0,
      "death_reason": 0,
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
      "vehicle_descr": 10369,
      "turret_id": 14979,
      "gun_id": 14468,
      "chassis_id": 15234,
      "squad_index": 0,
      "damage_blocked": 1470
    },
    {
      "team": 2,
      "name": "FALOSS_VOIN",
      "entity_id": 10361639,
      "dbid": 588636999,
      "clanid": 186043,
      "clan_tag": "DNLA",
      "hitpoints_left": 1185,
      "credits": 14194,
      "exp": 1076,
      "shots_made": 10,
      "shots_hit": 8,
      "shots_splash": 0,
      "shots_pen": 6,
      "damage_made": 2371,
      "damage_received": 715,
      "damage_assisted": 105,
      "damage_assisted_track": 0,
      "hits_received": 3,
      "hits_bounced": 1,
      "hits_splash": 0,
      "hits_pen": 2,
      "enemies_spotted": 3,
      "enemies_damaged": 4,
      "enemies_destroyed": 0,
      "time_alive": 229,
      "distance_travelled": 660,
      "killed_by": 0,
      "base_capture_points": 0,
      "base_defend_points": 0,
      "exp_for_damage": 272,
      "exp_for_assist": 4,
      "exp_team_bonus": 521,
      "wp_points_earned": 0,
      "wp_points_stolen": 0,
      "hero_bonus_credits": 0,
      "hero_bonus_exp": 0,
      "death_reason": -1,
      "achievements": [
        {
          "t": 476,
          "v": 83
        },
        {
          "t": 401,
          "v": 33
        },
        {
          "t": 407,
          "v": 2
        },
        {
          "t": 418,
          "v": 13
        }
      ],
      "vehicle_descr": 10369,
      "turret_id": 14979,
      "gun_id": 14468,
      "chassis_id": 15234,
      "squad_index": 0,
      "damage_blocked": 470
      }
    ],
    "exp_total": 888,
    "credits_total": 30523,
    "repair_cost": 0,
    "exp_free": 188,
    "exp_free_base": 29,
    "exp_penalty": 0,
    "credits_penalty": 0,
    "credits_contribution_in": 0,
    "credits_contribution_out": 0,
    "camouflage_id": -1
    }

    """


class ReplaySummary(JSONExportable):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )
    # fmt: off
    id                  : str
    map_id              : int
    battle_duration     : float
    title               : Optional[str] = None
    player_name         : str
    protagonist         : int
    vehicle_descr       : int
    mastery_badge       : MasteryBadge = Field(default=MasteryBadge.no)
    exp_base            : int = Field(default=0)
    enemies_spotted     : int = Field(default=0)
    enemies_destroyed   : int = Field(default=0)
    damage_assisted     : int = Field(default=0)
    damage_made         : int = Field(default=0)
    details_url         : Optional[AnyUrl] = Field(default=None)
    download_url        : Optional[AnyUrl] = Field(default=None)
    game_version        : Mapping[str, Any]
    arena_unique_id     : str
    # fmt: on

    @field_validator(
        "exp_base",
        "enemies_spotted",
        "enemies_destroyed",
        "damage_assisted",
        "damage_made",
        "mastery_badge",
        mode="before",
    )
    @classmethod
    def validate_none(cls, value: str | None) -> str:
        if value is None:
            return "0"
        else:
            return value


class ReplayRequest(JSONExportable):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )
    # fmt: off
    title       : Optional[str] = Field(None, min_length=1)
    private     : Optional[bool] = Field(default=None)
    upload_url  : Optional[AnyUrl] = Field(default=None)
    upload_file : Optional[bytes] = Field(default=None)
    # fmt: on


class Shot(JSONExportable):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )
    time: float
    shooter: int
    target: int
    has_damage: bool
    shell_id: int
    turret_yaw: float
    gun_pitch: float
    segment: str
    distance: float
    nominal_pen: int
    nominal_damage: int
    damage: int


class BattleDetails(JSONExportable):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )
    id: str
    map_id: int
    battle_type: int
    room_type: int
    data_version: int
    game_version: Mapping[str, Any]
    winner_team: int
    battle_start_time: AwareDatetime
    tier: int
    has_team1: bool
    has_team2: bool
    last_accessed_time: AwareDatetime
    chat: Sequence[ChatMessage]
    shots: Sequence[Shot]
    properties_json: Mapping[str, Any]


class HeatmapSet(JSONExportable):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )
    timestamp: int = Field(..., ge=0, le=4294967295)
    short_description: str
    long_description: str
    package: str = Field(..., max_length=32)
    version: int = Field(..., ge=-2147483648, le=2147483647)
    platform: PlatformEnum
    locked_maps: str = Field(..., max_length=256)


class PaginatedProductList(JSONExportable):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )
    count: Optional[int] = Field(None, examples=[123])
    next: Optional[AnyUrl] = Field(
        None, examples=["http://api.example.org/accounts/?page=4"]
    )
    previous: Optional[AnyUrl] = Field(
        None, examples=["http://api.example.org/accounts/?page=2"]
    )
    results: Optional[Sequence[Product]] = None


class PaginatedReplayList(JSONExportable):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )
    next: Optional[AnyUrl] = Field(
        None, examples=["http://api.example.org/accounts/?page=4"]
    )
    previous: Optional[AnyUrl] = Field(
        None, examples=["http://api.example.org/accounts/?page=2"]
    )
    results: Optional[List[ReplaySummary]] = None


class WoTinspector:
    """WoTinspector.com API v2 client"""

    URL_BASE: str = "https://api.wotinspector.com/v2"
    URL_REPLAYS: str = URL_BASE + "/blitz/replays/"

    DEFAULT_RATE_LIMIT: float = 20 / 3600  # 20 requests / hour

    def __init__(
        self, rate_limit: float = DEFAULT_RATE_LIMIT, auth_token: Optional[str] = None
    ) -> None:
        debug(f"rate_limit={rate_limit}, auth_token={auth_token}")
        headers: Optional[dict[str, str]] = None
        if auth_token is not None:
            headers = dict()
            headers["Api-Key"] = f"Token {auth_token}"

        self.session = ThrottledClientSession(
            rate_limit=rate_limit,
            filters=[self.URL_REPLAYS],
            re_filter=False,
            limit_filtered=True,
            headers=headers,
        )

    async def close(self) -> None:
        if self.session is not None:
            debug("Closing aiohttp session")
            await self.session.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    @classmethod
    def get_url_replay(cls, id: str) -> str:
        return f"{cls.URL_REPLAYS}{id}/"

    @classmethod
    def get_url_replay_list(cls, page: int = 1, **kwargs) -> str:
        kwargs["page"] = page
        return f"{cls.URL_REPLAYS}?{'&'.join([f'{k}={v}' for k,v in kwargs.items()])}"

    async def get_replay(self, id: str) -> Replay | None:
        """Get replay with id as Replay model"""
        return await get_model(
            self.session,
            self.get_url_replay(id),
            resp_model=Replay,
        )

    async def get_replay_list(
        self, page: int = 1, **kwargs
    ) -> List[ReplaySummary] | None:
        """Get list of replays"""
        debug(
            "starting: page=%d, %s",
            page,
            ", ".join([f"{k}={v}" for k, v in kwargs.items()]),
        )
        paginated_list: PaginatedReplayList | None
        if (
            paginated_list := await get_model(
                self.session,
                url=self.get_url_replay_list(page=page, **kwargs),
                resp_model=PaginatedReplayList,
            )
        ) is not None:
            return paginated_list.results
        message("could not retrieve valid replay list")
        return None

    class AsyncReplayIterable(AsyncIterable[ReplaySummary]):
        """Async iterable ovar API v2' replays list"""

        def __init__(
            self, wi: WoTinspector, page: int = 1, max_pages: int = 10, **filter_args
        ) -> None:
            super().__init__()
            self._filter_args: Dict[str, Any] = filter_args
            self._wi: WoTinspector = wi
            self._replay_list: List[ReplaySummary] | None = None
            self._index: int = -1  # must be -1 to work during the first time
            self._page: int = page
            self._max_pages: int = max_pages

        def __aiter__(self) -> Self:
            return self

        async def __anext__(self) -> ReplaySummary:
            self._index += 1
            if self._replay_list is None or self._index == len(self._replay_list):
                replay_list: List[ReplaySummary] | None
                if (
                    self._max_pages == 0
                    or (
                        replay_list := await self._wi.get_replay_list(
                            page=self._page, **self._filter_args
                        )
                    )
                    is None
                ):
                    raise StopAsyncIteration
                self._replay_list = replay_list
                self._page += 1
                self._max_pages -= 1
                self._index = -1
            if self._replay_list is not None and self._index < len(self._replay_list):
                return self._replay_list[self._index]
            raise StopAsyncIteration

    def list_replays(
        self, page: int = 1, max_pages: int = 10, **filter_args
    ) -> AsyncReplayIterable:
        return WoTinspector.AsyncReplayIterable(
            self, page=page, max_pages=max_pages, **filter_args
        )

    async def post_replay(
        self,
        replay: Path | str | bytes,
        title: str | None = None,
        priv: bool = False,
        tankopedia: WGApiWoTBlitzTankopedia | None = None,  # to auto-title
        maps: Maps | None = None,  # to auto-title
    ) -> Replay | None:
        """
        Post a WoT Blitz replay file to api.WoTinspector.com using API v2

        Returns 'Replay' model
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

            data = FormData()
            data.add_field(name="title", value=title)
            data.add_field(name="private", value=str(priv))
            data.add_field(name="upload_file", value=replay_file.data)

            # data = {
            #     "title": title,
            #     "private": str(priv),
            #     "upload_file": replay_file.data,
            # }
        except BadZipFile as err:
            error(f"corrupted replay file: {filename}")
            return None
        except KeyError as err:
            error(f"Unexpected KeyError: {err}")
            return None

        try:
            if (
                res := await post_url(
                    self.session,
                    url=self.URL_REPLAYS,
                    # headers=headers,
                    data=data,
                    retries=1,
                )
            ) is None:
                error(f"received NULL response")
            else:
                debug("response from %s: %s", self.URL_REPLAYS, res)
                return Replay.parse_str(res)
        except Exception as err:
            error(f"Unexpected Error: {type(err)}: {err}")
        return None
