from datetime import datetime, date
from time import time
from typing import Any, Mapping, Optional, Tuple, ClassVar, TypeVar
from os.path import basename
from enum import Enum, IntEnum, StrEnum
from collections import defaultdict
import logging
import aiofiles
import json
from bson.objectid import ObjectId
from bson.int64 import Int64
from isort import place_module
from pydantic import BaseModel, Extra, root_validator, validator, Field, HttpUrl, ValidationError
from pydantic.utils import ValueItems

from pyutils.utils import CSVExportable, CSVImportable, CSVImportableSelf, \
							TXTExportable, TXTImportable, JSONExportable, \
							JSONImportable, TypeExcludeDict, epoch_now



TYPE_CHECKING = True
logger = logging.getLogger()
error 	= logger.error
message	= logger.warning
verbose	= logger.info
debug	= logger.debug


class Region(StrEnum):
	ru 		= 'ru'
	eu 		= 'eu'
	com 	= 'com'
	asia 	= 'asia'
	china 	= 'china'
# #	API		= 'API'

	

	@classmethod
	def API_regions(cls) -> set['Region']:
		return { Region.eu, Region.com, Region.asia, Region.ru }


	@classmethod
	def has_stats(cls) -> set['Region']:
		return { Region.eu, Region.com, Region.asia, Region.ru }


	@classmethod
	def from_id(cls, account_id : int) -> Optional['Region']:
		try:
			if account_id >= 31e8:
				return Region.china
			elif account_id >= 20e8:
				return Region.asia
			elif account_id >= 10e8:
				return Region.com
			elif account_id >= 5e8:
				return Region.eu
			else:			
				return Region.ru
		except Exception as err:
			raise ValueError(f'accunt_id {account_id} is out of known id range: {err}')
		return None

	
	def matches(self, other_region : 'Region') -> bool:
		assert type(other_region) is type(self), 'other_region is not Region'
		return self == other_region

TypeAccountDict = dict[str, int|bool|Region|None]


class Account(JSONExportable, JSONImportable, CSVExportable, CSVImportable, 
				TXTExportable, TXTImportable):	

	id					: int 		 	= Field(default=..., alias='_id')
	region 				: Region | None	= Field(default=None, alias='r')
	last_battle_time	: int 	 | None	= Field(default=None, alias='l')

	_exclude_export_DB_fields  = None
	_exclude_export_src_fields = None

	class Config:
		allow_population_by_field_name = True
		allow_mutation 		= True
		validate_assignment = True		

	
	@validator('id')
	def check_id(cls, v):
		assert v is not None, "id cannot be None"
		assert isinstance(v, int), "id has to be int"
		if isinstance(v, Int64):
			v = int(v)
		if v < 0:
			raise ValueError('account_id must be >= 0')
		return v

	
	@validator('last_battle_time')
	def check_epoch_ge_zero(cls, v):
		if v is None:
			return None
		elif v >= 0:
			return v
		else:
			raise ValueError('time field must be >= 0')


	@root_validator(skip_on_failure=True)
	def set_region(cls, values: TypeAccountDict) -> TypeAccountDict:
		i = values.get('id')
		assert isinstance(i, int), f'_id has to be int, was: {i} : {type(i)}'
		if values.get('region') is None:
			# set default regions, but do not change region if set
			values['region'] = Region.from_id(i)
		return values


	# TXTExportable()
	def txt_row(self, format : str = 'id') -> str:
		"""export data as single row of text	"""
		if format == 'id':
			return str(self.id)
		else:
			raise ValueError(f'Unsupported export format: {format}')


	# TXTImportable()
	@classmethod
	def from_txt(cls, text : str) -> 'Account':
		"""export data as single row of text	"""
		try:
			return Account(id=int(text))
		except Exception as err:
			raise ValueError(f'Could not create Account() with id={text}: {err}')


	# CSVExportable()
	def csv_headers(self) -> list[str]:
		"""Provide CSV headers as list"""
		return list(self.dict(exclude_unset=False, by_alias=False).keys())
		
		
	def csv_row(self) -> dict[str, str | int | float | bool]:
		"""Provide instance data as dict for csv.DictWriter"""
		res : dict[str, str | int | float | bool] =  self.dict(exclude_unset=False, by_alias=False)
		if self.region is not None:
			res['region'] = self.region.value
		else:
			raise ValueError(f'Account {self.id} does not have region defined')
		return res
	

	def __str__(self) -> str:
		fields : list[str] = [ f for f in self.__fields__.keys() if f != 'id' ]
		return f'{type(self).__name__} id={self.id}: { ", ".join( [ f + "=" + str(getattr(self,f)) for f in fields ]  ) }'


class EnumWinnerTeam(IntEnum):
	draw = 0
	one = 1
	two = 2


class EnumBattleResult(IntEnum):
	incomplete = -1
	not_win = 0
	win = 1
	loss = 2
	draw = 3

	def __str__(self) -> str:
		return f'{self.name}'.capitalize()


class EnumVehicleTypeInt(IntEnum):
	light_tank 	= 0
	medium_tank = 1
	heavy_tank 	= 2
	tank_destroyer = 3

	def __str__(self) -> str:
		return f'{self.name}'.replace('_', ' ').capitalize()

	
	def as_str(self) -> 'EnumVehicleTypeStr':
		return EnumVehicleTypeStr[self.name]


	@classmethod
	def from_str(cls, t: str) -> 'EnumVehicleTypeInt':
		return EnumVehicleTypeStr(t).as_int()



class EnumVehicleTypeStr(StrEnum):
	light_tank 		= 'lightTank'
	medium_tank 	= 'mediumTank'
	heavy_tank 		= 'heavyTank'
	tank_destroyer	= 'AT-SPG'

	def __str__(self) -> str:
		return f'{self.name}'.replace('_', ' ').capitalize()


	def as_int(self) -> EnumVehicleTypeInt:
		return EnumVehicleTypeInt[self.name]


	@classmethod
	def from_int(cls, t: int) -> 'EnumVehicleTypeStr':
		return EnumVehicleTypeInt(t).as_str()



class EnumVehicleTier(IntEnum):
	I 		= 1
	II 		= 2
	III 	= 3
	IV 		= 4
	V 		= 5
	VI 		= 6
	VII 	= 7
	VIII 	= 8
	IX 		= 9
	X		= 10

	def __str__(self) -> str:
		return str(self.name)


class EnumNation(IntEnum):
	ussr		= 0
	germany		= 1
	usa 		= 2
	china 		= 3
	france		= 4
	uk			= 5
	japan		= 6
	other		= 7
	european	= 8

	def __str__(self) -> str:
		if self.value in [ 0 , 2, 5]:
			return f'{self.name}'.upper()
		else:
			return f'{self.name}'.capitalize()


WGBlitzReleaseSelf = TypeVar('WGBlitzReleaseSelf', bound='WGBlitzRelease')
class WGBlitzRelease(JSONExportable, JSONImportable, CSVExportable, CSVImportable, TXTExportable):
	release : str					= Field(default=..., alias='_id')
	launch_date: datetime | None	= Field(default=None)
	#_export_DB_by_alias			: bool = False

	class Config:		
		allow_mutation 			= True
		validate_assignment 	= True
		allow_population_by_field_name = True
		json_encoders 			= { datetime: lambda v: v.date().isoformat() }

	@validator('release')
	def validate_release(cls, v: str):
		"""Blitz release is format X.Y[.Z]"""
		rel: list[int] = cls._release_number(v)
		return cls._release_str(rel)


	@validator('launch_date', pre=True)
	def validate_date(cls, d):
		if d is None:
			return None
		elif isinstance(d, str):
			return datetime.combine(date.fromisoformat(d), datetime.min.time())
		elif isinstance(d,float):
			return int(d)
		elif isinstance(d, datetime):
			return datetime.combine(d.date(), datetime.min.time())
		elif isinstance(d, date):
			return datetime.combine(d, datetime.min.time())
		

	@classmethod
	def _release_number(cls, rel: str) -> list[int]:
		"""Return release in type list[int]"""
		return [ int(r) for r in rel.split('.')]


	@classmethod
	def _release_str(cls, rel: list[int]) -> str:
		"""Create a release string from list[int]"""
		return '.'.join([ str(r) for r in rel ])


	# TXTExportable()
	def txt_row(self, format : str = '') -> str:
		"""export data as single row of text"""
		return self.release


	# CSVExportable()
	def csv_headers(self) -> list[str]:
		return list(self.dict(exclude_unset=False, by_alias=False).keys())


	def csv_row(self) -> dict[str, str | int | float | bool]:
		res : dict[str, Any] =  self.dict(exclude_unset=False, by_alias=False)
		if 'launch_date' in res and res['launch_date'] is not None:
			res['launch_date'] = res['launch_date'].date()
		return self.clear_None(res)


	# # CSVImportable()
	# @classmethod
	# def from_csv(cls: type[CSVImportableSelf], row: dict[str, Any]) -> CSVImportableSelf | None:
	# 	"""Provide CSV row as a dict for csv.DictWriter"""
	# 	try:
	# 		row = cls._set_field_types(row)
	# 		debug(str(row))
	# 		return cls.parse_obj(row)
	# 	except Exception as err:
	# 		error(f'Could not parse row ({row}): {err}')
	# 	return None


	def next(self: WGBlitzReleaseSelf, **kwargs) -> WGBlitzReleaseSelf:
		rel : list[int] = self._release_number(self.release)
		major : int = rel[0]
		minor : int = rel[1]
		if minor < 10:
			minor += 1
		else:
			minor = 0
			major += 1
		return type(self)(release=self._release_str([major, minor]), **kwargs)
		

	def __eq__(self, __o: object) -> bool:
		return __o is not None and isinstance(__o, WGBlitzRelease) and \
					self.release == __o.release


	def __str__(self) -> str:
		return self.release
	
class WoTBlitzReplayAchievement(BaseModel):
	t: int
	v: int


# WoTBlitzReplayDetail = dict[str, Union[str, int, list[WoTBlitzReplayAchievement], None]]
class WoTBlitzReplayDetail(BaseModel):
	achievements : list[WoTBlitzReplayAchievement] | None = Field(default=None, alias='a')
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

	class Config:
		extra 				= Extra.allow
		allow_mutation 		= True
		validate_assignment = True
		allow_population_by_field_name = True


class WoTBlitzReplaySummary(BaseModel):
	_TimestampFormat : str = "%Y-%m-%d %H:%M:%S"

	winner_team 	: EnumWinnerTeam 	| None 	= Field(default=..., alias='wt')
	battle_result 	: EnumBattleResult 	| None 	= Field(default=..., alias='br')
	room_type		: int | None 	= Field(default=None, alias='rt')
	battle_type		: int | None 	= Field(default=None, alias='bt')
	uploaded_by 	: int 			= Field(default=0, alias='ul')
	title 			: str | None 	= Field(default=..., alias='t')
	player_name		: str			= Field(default=..., alias='pn')
	protagonist		: int 			= Field(default=..., alias='p')
	protagonist_team: int | None	= Field(default=..., alias='pt')
	map_name		: str			= Field(default=..., alias='mn')
	vehicle			: str			= Field(default=..., alias='v')
	vehicle_tier	: int | None	= Field(default=..., alias='vx')
	vehicle_type 	: EnumVehicleTypeInt | None = Field(default=..., alias='vt')
	credits_total	: int | None 	= Field(default=None, alias='ct')
	credits_base	: int | None 	= Field(default=None, alias='cb')
	exp_base		: int | None	= Field(default=None, alias='eb')
	exp_total		: int | None	= Field(default=None, alias='et')
	battle_start_timestamp : int	= Field(default=..., alias='bts')
	battle_start_time : str | None	= Field(default=None, repr=False)	# duplicate of 'bts'
	battle_duration : float			= Field(default=..., alias='bd')
	description		: str |None		= Field(default=None, alias='de')
	arena_unique_id	: int			= Field(default=..., alias='aid')
	allies 			: list[int]		= Field(default=..., alias='a')
	enemies 		: list[int]		= Field(default=..., alias='e')
	mastery_badge	: int | None 	= Field(default=None, alias='mb')
	details 		: list[WoTBlitzReplayDetail] = Field(default=..., alias='d')


	class Config:
		extra 				= Extra.allow
		allow_mutation 		= True
		validate_assignment = True
		allow_population_by_field_name = True


	@validator('vehicle_tier')
	def check_tier(cls, v : int | None) -> int | None:
		if v is not None:
			if v > 10 or v < 0:
				raise ValueError('Tier has to be within [1, 10]')
		return v


	@validator('protagonist_team')
	def check_protagonist_team(cls, v : int) -> int:
		if v == 1 or v == 2:
			return v
		else:
			raise ValueError('protagonist_team has to be within 1 or 2')


	@validator('battle_start_time')
	def return_none(cls, v : str) -> None:
		return None


	@root_validator(skip_on_failure=True)
	def root(cls, values : dict[str, Any]) ->  dict[str, Any]:
		values['battle_start_time'] = datetime.fromtimestamp(values['battle_start_timestamp']).strftime(cls._TimestampFormat)
		return values


class WoTBlitzReplayData(BaseModel):
	view_url	: HttpUrl 		= Field(default=None, alias='v')
	download_url: HttpUrl 		= Field(default=None, alias='d')
	id 			: str | None	= Field(default=None)
	summary		: WoTBlitzReplaySummary  = Field(default=..., alias='s')

	_ViewUrlBase : str = 'https://replays.wotinspector.com/en/view/'
	_DLurlBase	: str = 'https://replays.wotinspector.com/en/download/'

	class Config:
		arbitrary_types_allowed = True
		allow_mutation 			= True
		validate_assignment 	= True
		allow_population_by_field_name = True
		json_encoders = { ObjectId: str }


	@root_validator
	def store_id(cls, values : dict[str, Any]) -> dict[str, Any]:
		try:
			debug('validating: WoTBlitzReplayData()')
			id : str
			if values['id'] is not None:
				debug('data.id found')
				id = values['id']
			elif values['view_url'] is not None:
				id = values['view_url'].split('/')[-1:][0]
			elif values['download_url'] is not None:
				id = values['download_url'].split('/')[-1:][0]
			else:
				debug('could not modify id')
				return values  # could not modify 'id'
				# raise ValueError('Replay ID is missing')
			values['id']			= id
			values['view_url'] 		= f"{cls._ViewUrlBase}{id}"
			values['download_url'] 	= f"{cls._DLurlBase}{id}"
			return values
		except Exception as err:
			raise ValueError(f'Error reading replay ID: {err}')

		
class WoTBlitzReplayJSON(JSONExportable, JSONImportable):
	id 		: str | None 		= Field(default=None, alias='_id')
	status	: str				= Field(default="ok", alias='s')
	data	: WoTBlitzReplayData= Field(default=..., alias='d')
	error	: dict				= Field(default={}, alias='e')
	_URL_REPLAY_JSON : str 		= 'https://api.wotinspector.com/replay/upload?details=full&key='

	_exclude_export_src_fields 	= { 'id': True, 'data': { 'id': True }}
	_exclude_export_DB_fields	= { 'data': {
											'id': True,
											'view_url': True,
											'download_url': True,
											'summary': { 'battle_start_time' }
											}
									}

	class Config:
		arbitrary_types_allowed = True
		json_encoders 			= { ObjectId: str }
		allow_mutation 			= True
		validate_assignment 	= True
		allow_population_by_field_name = True


	@root_validator(pre=False)
	def store_id(cls, values : dict[str, Any]) -> dict[str, Any]:
		try:
			debug('validating: WoTBlitzReplayJSON(pre=False)')
			if 'id' not in values or values['id'] is None:
				values['id'] = values['data'].id
				debug(f"adding ROOT.id")
			elif 'id' in values and values['id'] is not None:
				debug(f"adding data.id from ROOT.id")
				values['data'].id = values['id']		
			return values
		except Exception as err:
			raise ValueError(f'Could not store replay ID: {err}')


	def get_id(self) -> str | None:
		try:
			if self.id is not None:
				return self.id
			else:
				return self.data.id
		except Exception as err:
			error(f'Could not read replay id: {err}')
		return None


	def get_url_json(self) -> str:
		return f'{self._URL_REPLAY_JSON}{self.id}'


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


	def get_platoons(self, player: int | None = None) -> Tuple[	defaultdict[int, list[int]],
																defaultdict[int, list[int]]]:
		allied_platoons : defaultdict[int, list[int]] = defaultdict(list)
		enemy_platoons 	: defaultdict[int, list[int]] = defaultdict(list)

		allies 	= self.get_allies(player)

		for d in self.data.summary.details:
			if d.squad_index is not None and d.squad_index > 0:
				account_id = d.dbid
				if account_id in allies:
					allied_platoons[d.squad_index].append(account_id)
				else:
					enemy_platoons[d.squad_index].append(account_id)

		return allied_platoons, enemy_platoons


	def get_battle_result(self, player : int | None = None) -> EnumBattleResult:
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
			raise Exception('Error reading replay')


class WGApiError(BaseModel):
	code: 	int | None
	message:str | None
	field: 	str | None
	value: 	str | None

	def str(self) -> str:
		return f'code: {self.code} {self.message}'

class WGtankStatAll(BaseModel):
	spotted			: int = Field(..., alias='sp')
	hits			: int = Field(..., alias='h')
	frags			: int = Field(..., alias='k')
	max_xp			: int | None
	wins 			: int = Field(..., alias='w')
	losses			: int = Field(..., alias='l')
	capture_points 	: int = Field(..., alias='cp')
	battles			: int = Field(..., alias='b')
	damage_dealt	: int = Field(..., alias='dd')
	damage_received	: int = Field(..., alias='dr')
	max_frags		: int = Field(..., alias='mk')
	shots			: int = Field(..., alias='sp')
	frags8p			: int | None
	xp				: int | None
	win_and_survived: int = Field(..., alias='ws')
	survived_battles: int = Field(..., alias='sb')
	dropped_capture_points: int = Field(..., alias='dp')

	class Config:		
		allow_mutation 			= True
		validate_assignment 	= True
		allow_population_by_field_name = True


	@validator('frags8p', 'xp', 'max_xp')
	def unset(cls, v: int | bool | None) -> None:
		return None



class WGtankStat(JSONExportable, JSONImportable):
	id					: ObjectId | None = Field(default=None, alias='_id')
	region				: Region | None = Field(default=None, alias='r')
	all					: WGtankStatAll = Field(..., alias='s')
	last_battle_time	: int			= Field(..., alias='lb')
	account_id			: int			= Field(..., alias='a')
	tank_id				: int 			= Field(..., alias='t')
	mark_of_mastery		: int 			= Field(..., alias='m')
	battle_life_time	: int 			= Field(..., alias='l')
	release 			: str  | None 	= Field(default=None, alias='u')
	max_xp				: int  | None
	in_garage_updated	: int  | None
	max_frags			: int  | None
	frags				: int  | None
	in_garage 			: bool | None

	_exclude_export_DB_fields	: ClassVar[Optional[TypeExcludeDict]] = {'max_frags': True, 'frags' : True, 
																		'max_xp': True, 'in_garage': True, 
																		'in_garage_updated': True 
																		}
	_exclude_export_src_fields	: ClassVar[Optional[TypeExcludeDict]] = {'region': True } 
	# _include_export_DB_fields	: ClassVar[Optional[TypeExcludeDict]] = None
	# _include_export_src_fields	: ClassVar[Optional[TypeExcludeDict]] = None

	class Config:
		arbitrary_types_allowed = True
		json_encoders 			= { ObjectId: str }
		allow_mutation 			= True
		validate_assignment 	= True
		allow_population_by_field_name = True


	@classmethod
	def mk_id(cls, account_id: int, last_battle_time: int, tank_id: int = 0) -> ObjectId:
		return ObjectId(hex(account_id)[2:].zfill(10) + hex(tank_id)[2:].zfill(6) + hex(last_battle_time)[2:].zfill(8))


	@validator('last_battle_time', pre=True)
	def validate_lbt(cls, v: int) -> int:
		now : int = epoch_now()
		if v > now + 36000:
			return now
		else:
			return v


	@root_validator(pre=False)
	def set_id(cls, values : dict[str, Any]) -> dict[str, Any]:
		try:
			if values['id'] is None:
				values['id'] = cls.mk_id(values['account_id'], values['last_battle_time'], values['tank_id'])				
			if 'region' not in values or values['region'] is None:
				values['region'] = Region.from_id(values['account_id'])
			return values
		except Exception as err:
			raise ValueError(f'Could not store _id: {err}')


	@validator('max_frags', 'frags', 'max_xp', 'in_garage', 'in_garage_updated')
	def unset(cls, v: int | bool | None) -> None:
		return None


class WGApiWoTBlitz(BaseModel):
	status	: str	= Field(default="ok", alias='s')
	meta	: dict[str, Any] 	| None	
	error	: WGApiError 		| None

	@validator('error')
	def if_error(cls, v : WGApiError | None) -> WGApiError | None:
		if v is not None:
			error(v.str())
		return v


class WGApiWoTBlitzTankStats(WGApiWoTBlitz):	
	data	: dict[str, list[WGtankStat] | None ] | None = Field(default=..., alias='d')

	class Config:		
		allow_mutation 			= True
		validate_assignment 	= True
		allow_population_by_field_name = True


class Tank(JSONExportable, JSONImportable):
	tank_id 	: int				= Field(default=..., alias='_id')
	name 		: str | None		= Field(default=None, alias='n')
	nation	: EnumNation | None 	= Field(default=None, alias='c')
	type: EnumVehicleTypeStr|None	= Field(default=None, alias='v')
	tier: EnumVehicleTier|None 		= Field(default=None, alias='t')
	is_premium 	: bool 				= Field(default=False, alias='p')
	next_tanks	: list[int] | None	= Field(default=None, alias='s')

	@validator('next_tanks', pre=True)
	def next_tanks2list(cls, v):
		try:
			if v is not None:
				return [ int(k) for k in v.keys() ]
		except Exception as err:
			error(f"Error validating 'next_tanks': {err}")
		return None


	@validator('type', pre=True)
	def prevalidate_type(cls, v):
		if isinstance(v, int):
			return EnumVehicleTypeStr.from_int(v).value
		else:
			return v


	@validator('type')
	def validate_type(cls, v):
		if isinstance(v, str):
			return EnumVehicleTypeStr(v)
		else:
			return v


	@validator('tier', pre=True)
	def prevalidate_tier(cls, v: Any):
		if isinstance(v, str):
			return EnumVehicleTier[v.upper()].value
		else:
			return v
		

	@validator('tier')
	def validate_tier(cls, v):
		if isinstance(v, int):
			return EnumVehicleTier(v)
		else:
			return v


	@classmethod
	def from_id(cls, id : int) -> 'Tank':
		return Tank(tank_id=id)


	class Config:		
		allow_mutation 			= True
		validate_assignment 	= True
		allow_population_by_field_name = True
		use_enum_values			= True


class WGplayerAchievements(JSONExportable):
	

	class Config:		
		allow_mutation 			= True
		validate_assignment 	= True
		allow_population_by_field_name = True
		extra 					= Extra.allow


class WGplayerAchievementsMaxSeries(JSONExportable):
	id 			: ObjectId | None	= Field(default=None, alias='_id')
	jointVictory: int 				= Field(default=0, alias='jv')
	account_id	: int		 		= Field(default=0, alias='a')	
	region		: Region | None 	= Field(default=None, alias='r')
	release 	: str  | None 		= Field(default=None, alias='u')
	added		: int 				= Field(default=epoch_now(), alias='t')

	_include_export_DB_fields	: ClassVar[Optional[TypeExcludeDict]] = { 'jointVictory': True, 
																		'account_id': True, 
																		'region': True, 
																		'release': True 
																		}

	class Config:		
		allow_mutation 			= True
		validate_assignment 	= True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True
		json_encoders 			= { ObjectId: str }
		extra 				= Extra.allow
	

	@classmethod
	def mk_id(cls, account_id : int, region: Region | None, added: int) -> ObjectId:
		r: int = 0
		if region is not None:
			r = list(Region).index(region)
		return ObjectId(hex(account_id)[2:].zfill(10) + hex(r)[2:].zfill(6) + hex(added)[2:].zfill(8))
	

	@root_validator
	def set_region_id(cls, values: dict[str, Any]) -> dict[str, Any]:
		r: int = 0
		region : Region | None 	= values['region']
		account_id : int 		= values['account_id']

		if region is None and account_id > 0:
			region = Region.from_id(account_id)
		values['region'] = region
		values['id'] = cls.mk_id(account_id, region, values['added'])
		return values

	# @root_validator(pre=False)
	# def set_id(cls, values : dict[str, Any]) -> dict[str, Any]:
	# 	try:
	# 		if values['id'] is None:
	# 			values['id'] = cls.mk_id(values['account_id'], values['last_battle_time'], values['tank_id'])				
	# 		if 'region' not in values or values['region'] is None:
	# 			values['region'] = Region.from_id(values['account_id'])
	# 		return values
	# 	except Exception as err:
	# 		raise ValueError(f'Could not store _id: {err}')



	@root_validator
	def set_region(cls, values: dict) -> dict:
		try:
			if values['region'] is None and values['account'] > 0:
				values['region'] = Region.from_id(values['account'])
		except:
			pass
		return values


class WGplayerAchievementsMain(JSONExportable):
	achievements 	: WGplayerAchievements | None = Field(default=None, alias='a')
	max_series		: WGplayerAchievementsMaxSeries | None = Field(default=None, alias='m')

	class Config:		
		allow_mutation 			= True
		validate_assignment 	= True
		allow_population_by_field_name = True


class WGApiWoTBlitzPlayerAchievements(WGApiWoTBlitz):	
	data	: dict[str, WGplayerAchievementsMain] | None = Field(default=None, alias='d')

	class Config:		
		allow_mutation 			= True
		validate_assignment 	= True
		allow_population_by_field_name = True


	def get_max_series(self) -> list[WGplayerAchievementsMaxSeries]:
		res : list[WGplayerAchievementsMaxSeries] = list()
		try:			
			if self.data is None:
				return res
			for key, pam in self.data.items():
				try:
					if pam.max_series is None:
						continue
					ms : WGplayerAchievementsMaxSeries = pam.max_series
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
					if pam.max_series is None:
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
	data : dict[str, Tank] | None = Field(default=..., alias='d')
	
	class Config:		
		allow_mutation 			= True
		validate_assignment 	= True
		allow_population_by_field_name = True
