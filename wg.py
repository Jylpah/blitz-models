import logging
from typing import Dict, Tuple, cast

from pydantic import BaseModel
from .models import Region, WGApiWoTBlitzTankStats, WGtankStat
from pyutils.throttledclientsession import ThrottledClientSession
from pyutils.utils import get_url_JSON_model, get_url

TYPE_CHECKING = True
logger = logging.getLogger()
error 	= logger.error
message	= logger.warning
verbose	= logger.info
debug	= logger.debug

class WGApi():

	# constants
	DEFAULT_WG_APP_ID 		: str = '81381d3f45fa4aa75b78a7198eb216ad'

	URL_SERVER = {
		'eu'    : 'https://api.wotblitz.eu/wotb/',
		'ru'    : 'https://api.wotblitz.ru/wotb/',
		'na'    : 'https://api.wotblitz.com/wotb/',
		'asia'  : 'https://api.wotblitz.asia/wotb/',
		'china' : None
		}

	def __init__(self, WG_app_id : str = DEFAULT_WG_APP_ID, 
				# tankopedia_fn 	: str = 'tanks.json', 
				# maps_fn 		: str = 'maps.json', 
				rate_limit: float = 10):
		assert WG_app_id is not None, "WG App ID must not be None"
		assert rate_limit is not None, "rate_limit must not be None"

		self.app_id : str = WG_app_id
		
		if self.app_id is not None:
			headers = {'Accept-Encoding': 'gzip, deflate'} 	
			self.session : Dict[str, ThrottledClientSession] | None = dict()
			for region in Region.API_regions():
				self.session[region.value] = ThrottledClientSession(rate_limit=rate_limit, headers=headers)
			debug('WG aiohttp session initiated')            
		else:
			self.session = None
			debug('WG aiohttp session NOT initiated')
		

	@classmethod
	def get_server_url(cls, region: Region) -> str | None:
		assert region is not None, "region must not be None"		
		try:
			return cls.URL_SERVER[region.value]
		except Exception as err:
			error(f'Unknown region: {region.value}')
		return None

	
	def tank_stats_get_url(self, account_id : int , region: Region | None = None, 
							tank_ids: list[int] = [], fields: list[str] = []) -> Tuple[str, Region] | None:
		assert type(account_id) is int, "account_id must be int"
		assert type(tank_ids) is list, "tank_ids must be a list"
		assert type(fields) is list, "fields must be a list"
		try:
			URL_WG_TANK_STATS: str = 'tanks/stats/'

			account_region : Region | None = Region.from_id(account_id)
			if account_region is None:
				raise ValueError('Could not determine region for account_id')

			if region is None:
				region = account_region
			else:
				if not region.matches(account_region):
					raise ValueError(f'account_id {account_id} does not match region {region.value}')
						
			server : str | None = self.get_server_url(account_region)
			if server is None:
				raise ValueError(f'No API server for region {account_region.value}')
			
			tank_id_str : str = ''
			if len(tank_ids) > 0:
				tank_id_str = '&tank_id=' + '%2C'.join([ str(x) for x in tank_ids])
			
			field_str : str = ''
			if len(fields) > 0:
				field_str = '&fields=' + '%2C'.join(fields)

			return f'{server}{URL_WG_TANK_STATS}?application_id={self.app_id}&account_id={account_id}{tank_id_str}{field_str}', account_region
		except Exception as err:
			debug(f'Failed to form url for account_id: {account_id}: {str(err)}')
		return None

	
	async def get_tank_stats_full(self, account_id: int, region: Region | None = None,
				tank_ids: list[int] = [], fields: list[str] = [] ) -> WGApiWoTBlitzTankStats | None:
		assert self.session is not None, "session must be initialized"
		try:
			server_url : Tuple[str, Region] | None = self.tank_stats_get_url(account_id=account_id, region=region, tank_ids=tank_ids, fields=fields)
			if server_url is None:
				raise ValueError(f'No tank stats available')
			url : str = server_url[0]
			region = server_url[1]

			resp : BaseModel | None = await get_url_JSON_model(self.session[region.value], url, resp_model=WGApiWoTBlitzTankStats)
			if resp is None:
				return None
			else:
				return cast(WGApiWoTBlitzTankStats, resp)
		except Exception as err:
			error(f'Failed to fetch tank stats for account_id: {account_id}: {str(err)}')
		return None	

	
	async def get_tank_stats(self, account_id: int, region: Region | None = None,
			tank_ids: list[int] = [], fields: list[str] = [] ) -> list[WGtankStat] | None:
		assert self.session is not None, "session must be initialized"
		try:
			resp : WGApiWoTBlitzTankStats | None = await self.get_tank_stats_full(account_id=account_id, region=region, tank_ids=tank_ids, fields=fields)
			if resp is None:
				return None
			else:
				return list(resp.data.values())[0]
		except Exception as err:
			verbose(f'Failed to fetch tank stats for account_id: {account_id}: {str(err)}')	# or DEBUG? 
		return None	
		

class Tankopedia():
	_tanks : Dict[int, Dict[str, int | str | bool]] | None = None


class Maps():
	_maps : Dict[str, str] = {
		"Random": "Random map",
		"amigosville": "Falls Creek",
		"asia": "Lost Temple",
		"canal": "Canal",
		"canyon": "Canyon",
		"desert_train": "Desert Sands",
		"erlenberg": "Middleburg",
		"faust": "Faust",
		"fort": "Macragge",
		"grossberg": "Dynasty's Pearl",
		"himmelsdorf": "Himmelsdorf",
		"italy": "Vineyards",
		"karelia": "Rockfield",
		"karieri": "Copperfield",
		"lake": "Mirage",
		"lumber": "Alpenstadt",
		"malinovka": "Winter Malinovka",
		"medvedkovo": "Dead Rail",
		"milbase": "Yamato Harbor",
		"mountain": "Black Goldville",
		"north": "North",
		"ordeal": "Trial by Fire",
		"pliego": "Castilla",
		"port": "Port Bay",
		"rock": "Mayan Ruins",
		"rudniki": "Mines",
		"savanna": "Oasis Palms",
		"skit": "Naval Frontier",
		"test": "World of Ducks",
		"tutorial": "Proving Grounds"
	}
		