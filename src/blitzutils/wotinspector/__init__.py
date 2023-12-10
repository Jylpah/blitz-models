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
)

from .wi_apiv1 import (
    WoTinspector as WoTinspector,
    WoTInspectorAPIReplays as WoTInspectorAPIReplays,
    WIReplaysData as WIReplaysData,
    ReplayFile as ReplayFile,
    ReplayFileMeta as ReplayFileMeta,
    ReplayJSON as ReplayJSON,
    ReplayData as ReplayData,
    ReplaySummary as ReplaySummary,
    ReplayDetail as ReplayDetail,
    ReplayAchievement as ReplayAchievement,
    WoTBlitzMaps as WoTBlitzMaps,
)

__all__ = [
    "wi_apiv1",  # Legacy, to be removed
    "wi_apiv2",
]
