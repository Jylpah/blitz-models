from enum import StrEnum

MAX_UINT32 : int = 4294967295

class Region(StrEnum):
	ru 		= 'ru'
	eu 		= 'eu'
	com 	= 'com'
	asia 	= 'asia'
	china 	= 'china'
	bot 	= 'BOTS'


	@classmethod
	def API_regions(cls) -> set['Region']:
		return { Region.eu, Region.com, Region.asia, Region.ru }


	@classmethod
	def has_stats(cls) -> set['Region']:
		return { Region.eu, Region.com, Region.asia, Region.ru }

	@property
	def id_range(self) -> range:
		if self == Region.ru:
			return range(0, int(5e8))
		elif self == Region.eu:
			return range(int(5e8), int(10e8))
		elif self == Region.com:
			return range(int(10e8), int(20e8))
		elif self == Region.asia:
			return range(int(20e8), int(31e8))
		elif self == Region.china:
			return range(int(31e8), int(42e8))
		else:
			return range(int(42e8), MAX_UINT32 + 1)
	
	@property
	def id_range_players(self) -> range:
		if self == Region.ru:
			return range(0, int(5e8))
		elif self == Region.eu:
			return range(int(5e8), int(10e8))
		elif self == Region.com:
			return range(int(10e8), int(20e8))
		elif self == Region.asia:
			return range(int(20e8), int(30e8))
		elif self == Region.china:
			return range(int(31e8), int(42e8))
		else:
			return range(int(42e8), MAX_UINT32 + 1)


	@classmethod
	def from_id(cls, account_id : int) -> 'Region':
		try:
			if account_id >= 42e8:
				return Region.bot  		# bots, same IDs on every server
			elif account_id >= 31e8:
				return Region.china
			elif account_id >= 20e8:
				return Region.asia
			elif account_id >= 10e8:
				return Region.com
			elif account_id >= 5e8:
				return Region.eu
			elif account_id >= 0:			
				return Region.ru
			else:
				raise ValueError(f'account_id is out of id_range: {account_id}')
		except Exception as err:
			raise ValueError(f'accunt_id {account_id} is out of known id range: {err}')

	
	def matches(self, other_region : 'Region') -> bool:
		assert type(other_region) is type(self), 'other_region is not Region'
		return self == other_region
