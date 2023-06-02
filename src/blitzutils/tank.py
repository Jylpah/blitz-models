import logging
import json
from warnings import warn
from typing import Any, Optional
from enum import IntEnum, StrEnum
from pydantic import root_validator, validator, Field, Extra

from pyutils import CSVExportable, TXTExportable,  JSONExportable, \
					CSVImportable, TXTImportable, JSONImportable, \
					Idx, BackendIndexType, BackendIndex
from pyutils.exportable import	DESCENDING, ASCENDING, TEXT

logger = logging.getLogger()
error 	= logger.error
message	= logger.warning
verbose	= logger.info
debug	= logger.debug


class EnumVehicleTypeInt(IntEnum):
	light_tank 	= 0
	medium_tank = 1
	heavy_tank 	= 2
	tank_destroyer = 3

	def __str__(self) -> str:
		return f'{self.name}'.replace('_', ' ').capitalize()


	@property
	def as_str(self) -> 'EnumVehicleTypeStr':
		return EnumVehicleTypeStr[self.name]


	@classmethod
	def from_str(cls, t: str) -> 'EnumVehicleTypeInt':
		return EnumVehicleTypeStr(t).as_int


class EnumVehicleTypeStr(StrEnum):
	light_tank 		= 'lightTank'
	medium_tank 	= 'mediumTank'
	heavy_tank 		= 'heavyTank'
	tank_destroyer	= 'AT-SPG'


	def __str__(self) -> str:
		return f'{self.name}'.replace('_', ' ').capitalize()


	@property
	def as_int(self) -> 'EnumVehicleTypeInt':
		return EnumVehicleTypeInt[self.name]


	@classmethod
	def from_int(cls, t: int) -> 'EnumVehicleTypeStr':
		return EnumVehicleTypeInt(t).as_str


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


	@classmethod
	def read_tier(cls, tier: str) -> 'EnumVehicleTier':
		try:
			if tier.isdigit():
				return EnumVehicleTier(int(tier))
			else:
				return EnumVehicleTier[tier]
		except Exception as err:
			raise ValueError(f"incorrect tier: '{tier}': {err}")


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




class WGTank(JSONExportable, JSONImportable):
	#id 			: int 						= Field(default=0, alias = '_id')
	tank_id 	: int 						= Field(default=..., alias = '_id')
	name   		: str | None				= Field(default=None)
	nation   	: EnumNation | None	 		= Field(default=None)
	type 	  	: EnumVehicleTypeStr| None	= Field(default=None)
	tier 		: EnumVehicleTier| None 	= Field(default=None)
	is_premium 	: bool 						= Field(default=False)


	class Config:		
		allow_mutation 			= True
		validate_assignment 	= True
		allow_population_by_field_name = True
		extra 					= Extra.allow


	@property
	def index(self) -> Idx:
		"""return backend index"""
		return self.tank_id


	@property
	def indexes(self) -> dict[str, Idx]:
		"""return backend indexes"""
		return { 'tank_id': self.index }


	@classmethod
	def backend_indexes(cls) -> list[list[tuple[str, BackendIndexType]]]:
		indexes : list[list[BackendIndex]] = list()
		indexes.append([ ('tier', ASCENDING), 
						 ('type', ASCENDING)
						])
		indexes.append([ ('tier', ASCENDING), 
						 ('nation', ASCENDING)
						])
		indexes.append([ ('name', TEXT) 							
						])		
		return indexes


	@validator('tank_id')
	def validate_id(cls, v: int) -> int:
		if v > 0:
			return v
		raise ValueError('id must be > 0')


	# @root_validator(pre=True)
	# def set_tank_id(cls, values: dict[str, Any])  -> dict[str, Any]:
	# 	if 'tank_id' in values:
	# 		values['id'] = values['tank_id']
	# 	elif '_id' in values:
	# 		values['tank_id'] = values['_id']
	# 	elif 'id' in values:
	# 		values['tank_id'] = values['id']
	# 	else:
	# 		raise ValueError("'tank_id' or 'id' is not defined")		
	# 	return values


	# @validator('tier')
	# def validate_tier(cls, v: int) -> int:
	# 	if v > 0 and v <= 10:
	# 		return v
	# 	raise ValueError('tier must be [0 ... 10]')

	# @validator('type')
	# def validate_type(cls, v: str) -> str:
	# 	if v in [ t.value for t in EnumVehicleTypeStr]:
	# 		return v
	# 	raise ValueError(f'Unknown tank type: {v}')


            return v
