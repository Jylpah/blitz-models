from .wg 			import WGApi as WGApi
from .wotinspector 	import WoTinspector as WoTinspector
from .replay 		import WoTBlitzReplayJSON as WoTBlitzReplayJSON,\
	 						WoTBlitzReplayData as WoTBlitzReplayData, \
							WoTBlitzReplaySummary as WoTBlitzReplaySummary, \
							WoTBlitzReplayDetail as WoTBlitzReplayDetail, \
							WoTBlitzReplayAchievement as WoTBlitzReplayAchievement, \
							WoTBlitzMaps as WoTBlitzMaps
from .region 		import Region as Region
from .release 		import WGBlitzRelease as WGBlitzRelease
from .account 		import Account as Account
from .tank 			import EnumNation as EnumNation, \
							EnumVehicleTier as EnumVehicleTier, \
							EnumVehicleTypeInt as EnumVehicleTypeInt, \
							EnumVehicleTypeStr as EnumVehicleTypeStr, \
							EnumVehicleType as EnumVehicleType, \
							Tank as Tank, \
							WGTank as WGTank
from .wg_api 		import WGAccountInfo as WGAccountInfo, \
	 					 	WGApiError as WGApiError, \
							WGApiWoTBlitz as WGApiWoTBlitz, \
							WGApiTankopedia as WGApiTankopedia, \
							WGApiWoTBlitzAccountInfo as WGApiWoTBlitzAccountInfo, \
							WGApiWoTBlitzPlayerAchievements as WGApiWoTBlitzPlayerAchievements, \
							WGApiWoTBlitzTankStats as WGApiWoTBlitzTankStats, \
							WGPlayerAchievements as WGPlayerAchievements, \
							WGPlayerAchievementsMain as WGPlayerAchievementsMain, \
							WGPlayerAchievementsMaxSeries as WGPlayerAchievementsMaxSeries, \
							WGTankStat as WGTankStat, \
							WGTankStatAll as WGTankStatAll, \
							WoTBlitzTankString as WoTBlitzTankString

__all__ = [ 'wg',
		   	'wg_api',
			'wotinspector',
			'release',
			'region',
			'account',
			'tank',
			]
