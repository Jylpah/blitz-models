from .wi_apiv2 import (
    BattleDetails as BattleDetails,
    ChatMessage as ChatMessage,
    GameVersion as GameVersion,
    HeatmapSet as HeatmapSet,
    MapEntry as MapEntry,
    PaginatedGameVersionList as PaginatedGameVersionList,
    PaginatedProductList as PaginatedProductList,
    PaginatedReplayList as PaginatedReplayList,
    PlatformEnum as PlatformEnum,
    PlayerData as PlayerData,
    Product as Product,
    Replay as Replay,
    ReplaySummary as ReplaySummary,
    ReplayRequest as ReplayRequest,
    Shot as Shot,
    WoTinspector as WoTinspector,
)

from .wi_apiv1 import (
    WoTInspectorAPIReplays as WoTInspectorAPIReplays,
    WIReplaysData as WIReplaysData,
    ReplayJSON as ReplayJSON,
    ReplayData as ReplayData,
    ReplayDetail as ReplayDetail,
    ReplayAchievement as ReplayAchievement,
    WoTBlitzMaps as WoTBlitzMaps,
    EnumWinnerTeam as EnumWinnerTeam,
    EnumBattleResult as EnumBattleResult,
    EnumVehicleTypeInt as EnumVehicleTypeInt,
)

__all__ = [
    "wi_apiv1",  # Legacy, to be removed
    "wi_apiv2",
]
