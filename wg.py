from typing import List, Dict, Optional
import aiohttp, json, re, sys, os, urllib, asyncio, logging, aiosqlite, time
from pyutils.throttledclientsession import ThrottledClientSession

## -----------------------------------------------------------
#### Class StatsNotFound 
## -----------------------------------------------------------

class StatsNotFound(Exception):
    pass

## -----------------------------------------------------------
#### Class WG 
## -----------------------------------------------------------

class WG:

    URL_WG_CLAN_INFO  		: str = 'clans/info/?application_id='
    #URL_WG_PLAYER_TANK_LIST : str = 'tanks/stats/?fields=tank_id%2Clast_battle_time&application_id='
    #URL_WG_PLAYER_TANK_LIST : str = 'tanks/stats/?fields=account_id%2Ctank_id%2Clast_battle_time%2Cbattle_life_time%2Call&application_id='
    URL_WG_PLAYER_TANK_STATS: str = 'tanks/stats/?application_id='
    URL_WG_ACCOUNT_ID     	: str = 'account/list/?fields=account_id%2Cnickname&application_id='
    URL_WG_PLAYER_STATS     : str = 'account/info/?application_id='
    URL_WG_PLAYER_ACHIEVEMENTS: str = 'account/achievements/?application_id='
    CACHE_DB_FILE           : str= '.blitzutils_cache.sqlite3' 
    CACHE_GRACE_TIME        : int =  30*24*3600  # 30 days cache
    TIME_SYNC_THRESHOLD     : int = 3*3600
    DEFAULT_WG_APP_ID 		: str = '81381d3f45fa4aa75b78a7198eb216ad'

    # sql_create_player_stats_tbl = """CREATE TABLE IF NOT EXISTS player_stats (
    #                             account_id INTEGER NOT NULL,
    #                             date INTEGER NOT NULL,
    #                             stat TEXT,
    #                             value FLOAT
    #                             ); """
    
    # sql_create_player_tank_stats_tbl = """CREATE TABLE IF NOT EXISTS player_tank_stats (
    #                         account_id INTEGER NOT NULL,
    #                         tank_id INTEGER DEFAULT NULL,
    #                         date INTEGER NOT NULL,
    #                         stat TEXT,
    #                         value FLOAT
    #                         ); """
    
    # sql_select_player_stats = """SELECT value FROM player_stats ORDERBY date ASC
    #                                 WHERE account_id = {} AND stat = {} 
    #                                 AND date >= {} LIMIT 1;"""
          
    
    SQL_TANK_STATS_TBL 	: str = 'tank_stats'

    SQL_TANK_STATS_CREATE_TBL : str  = 'CREATE TABLE IF NOT EXISTS ' + SQL_TANK_STATS_TBL + \
                                    """ ( account_id INTEGER NOT NULL, 
                                    tank_id INTEGER NOT NULL, 
                                    update_time INTEGER NOT NULL, 
                                    stats TEXT, 
                                    PRIMARY KEY (account_id, tank_id) )"""

    SQL_TANK_STATS_COUNT : str = 'SELECT COUNT(*) FROM ' + SQL_TANK_STATS_TBL

    SQL_TANK_STATS_UPDATE : str = 'REPLACE INTO ' + SQL_TANK_STATS_TBL + '(account_id, tank_id, update_time, stats) VALUES(?,?,?,?)'

    SQL_PLAYER_STATS_TBL  : str = 'player_stats'

    SQL_PLAYER_STATS_CREATE_TBL: str = 'CREATE TABLE IF NOT EXISTS ' + SQL_PLAYER_STATS_TBL + \
                                    """ ( account_id INTEGER PRIMARY KEY, 
                                    update_time INTEGER NOT NULL, 
                                    stats TEXT)"""

    SQL_PLAYER_STATS_COUNT : str = 'SELECT COUNT(*) FROM ' + SQL_PLAYER_STATS_TBL

    SQL_PLAYER_STATS_UPDATE : str = 'REPLACE INTO ' + SQL_PLAYER_STATS_TBL + '(account_id, update_time, stats) VALUES(?,?,?)'

    SQL_PLAYER_STATS_CACHED : str = 'SELECT * FROM ' +  SQL_PLAYER_STATS_TBL + ' WHERE account_id = ? AND update_time > ?'

    SQL_PLAYER_ACHIEVEMENTS_TBL : str = 'player_achievements'

    SQL_PLAYER_ACHIEVEMENTS_CREATE_TBL : str = 'CREATE TABLE IF NOT EXISTS ' + SQL_PLAYER_ACHIEVEMENTS_TBL + \
                                    """ ( account_id INTEGER PRIMARY KEY, 
                                    update_time INTEGER NOT NULL, 
                                    stats TEXT)"""

    SQL_PLAYER_ACHIEVEMENTS_CACHED : str = 'SELECT * FROM ' +  SQL_PLAYER_ACHIEVEMENTS_TBL + ' WHERE account_id = ? AND update_time > ?'

    SQL_PLAYER_ACHIEVEMENTS_UPDATE : str = 'REPLACE INTO ' + SQL_PLAYER_ACHIEVEMENTS_TBL + '(account_id, update_time, stats) VALUES(?,?,?)'

    SQL_PLAYER_ACHIEVEMENTS_COUNT  : str = 'SELECT COUNT(*) FROM ' + SQL_PLAYER_ACHIEVEMENTS_TBL

    SQL_TABLES : List[str]     = [ SQL_PLAYER_STATS_TBL, SQL_TANK_STATS_TBL, SQL_PLAYER_ACHIEVEMENTS_TBL ]

    SQL_CHECK_TABLE_EXITS : str = """SELECT name FROM sqlite_master WHERE type='table' AND name=?"""

    SQL_PRUNE_CACHE       : str = """DELETE from {} WHERE update_time < {}""" 

## Default data. Please use the latest maps.json

    maps : Dict[str, str] = {
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

    NATIONS : List[str] = [ 
        'ussr', 
        'germany', 
        'usa', 
        'china', 
        'france', 
        'uk', 
        'japan', 
        'other', 
        'european'
        ]

    NATION_ID : Dict[str, int] = {
        'ussr'      : 0,
        'germany'   : 1, 
        'usa'       : 2, 
        'china'     : 3,
        'france'    : 4,
        'uk'        : 5,
        'japan'     : 6,
        'other'     : 7,
        'european'  : 8
    }

    TANK_TYPE 	: List[str] 	= [ 
        'lightTank', 
        'mediumTank', 
        'heavyTank', 
        'AT-SPG' 
        ]

    TANK_TYPE_ID : Dict[str, int] = {
        'lightTank'     : 0,
        'mediumTank'    : 1,
        'heavyTank'     : 2,
        'AT-SPG'        : 3
        }

    URL_WG_SERVER : Dict[str, Optional[str]] = {
        'eu'    : 'https://api.wotblitz.eu/wotb/',
        'ru'    : 'https://api.wotblitz.ru/wotb/',
        'na'    : 'https://api.wotblitz.com/wotb/',
        'asia'  : 'https://api.wotblitz.asia/wotb/',
        'china' : None
        }

    ACCOUNT_ID_SERVER : Dict[str, List[int]]= {
        'ru'    : [ 0, int(5e8)],
        'eu'    : [ int(5e8), int(10e8) ],
        'na'    : [ int(1e9),int(2e9) ],
        'asia'  : [ int(2e9),int(31e8) ],
        'china' : [ int(31e8),int(4e9)]
        }

    ACCOUNT_ID_MAX = max(ACCOUNT_ID_SERVER['asia'])

    def __init__(self, WG_app_id : str = WG.DEFAULT_WG_APP_ID, 
                tankopedia_fn 	: str = 'tanks.json', 
                maps_fn 		: str = 'maps.json', 
                stats_cache: bool = False, 
                rate_limit: float = 10):
        
        self.WG_app_id : str = WG_app_id
        self.tanks : Dict
        self.load_tanks(tankopedia_fn)
        
        if (maps_fn is not None):
            if os.path.exists(maps_fn) and os.path.isfile(maps_fn):
                try:
                    with open(maps_fn, 'rt', encoding='utf8') as f:
                        self.maps = json.loads(f.read())
                except Exception as err:
                    logging.error('Could not read maps file: ' + maps_fn + '\n' + str(err))  
            else:
                logging.info('Could not find maps file: ' + maps_fn)    
        if self.WG_app_id is not None:
            headers = {'Accept-Encoding': 'gzip, deflate'} 	
            self.session : Dict[str, ThrottledClientSession] = dict()
            for server in list(self.URL_WG_SERVER)[:4]:    # China (5th) server is unknown, thus excluded
                self.session[server] = ThrottledClientSession(rate_limit=rate_limit, headers=headers)
            logging.debug('WG aiohttp session initiated')            
        else:
            self.session = None
            logging.debug('WG aiohttp session NOT initiated')
        
        # cache
        self.cache = None
        self.statsQ = None
        self.stat_saver_task = None
        if stats_cache:
            try:
                self.statsQ = asyncio.Queue()
                self.stat_saver_task = asyncio.create_task(self.stat_saver())
            except Exception as err:
                logging.error(str(err))
                sys.exit(1)
    

    async def close(self):
        # close stats queue 
        if self.statsQ is not None:
            logging.debug('WG.close(): Waiting for statsQ to finish')
            await self.statsQ.join()
            logging.debug('WG.close(): statsQ finished')
            self.stat_saver_task.cancel()
            logging.debug('statsCacheTask cancelled')
            await self.stat_saver_task 
                
        # close cacheDB
        if self.cache is not None:
            # prune old cache records
            await self.cleanup_cache()   
            await self.cache.commit()
            await self.cache.close()
        
        if self.session is not None:
            if self.global_rate_limit:
                await self.session.close()
            else:
                for server in self.session:
                    await self.session[server].close()
   
        return

    ## Class methods  ----------------------------------------------------------

    @classmethod
    def get_server(cls, account_id: int) -> Optional[str]:
        """Get Realm/server of an account based on account ID"""
        if account_id >= 1e9:
            if account_id >= 31e8:
                logging.debug('Chinese account/server: no stats available')
                return None
            if account_id >= 2e9:
                return 'asia'
            return 'na'
        else:
            if account_id < 5e8:
                return 'ru'
            return 'eu'
        return None


    @classmethod
    def update_maps(cls, map_data: dict):
        """Update maps data"""
        cls.maps = map_data


    @classmethod
    def get_map(cls, map_str: str) -> Optional[str]:
        """Return map name from short map string in replays"""
        try:
            return cls.maps[map_str]
        except:
            logging.error('Map ' + map_str + ' not found')
        return None
    

    @classmethod
    def get_map_user_strs(cls) -> str:
        return cls.maps.keys()


    @classmethod
    def get_tank_name(cls, tank_str: str) -> str:
        """Return tank name from short tank string in replays"""
        try:
            return cls.tanks["userStr"][tank_str]
        except:
            logging.error('Tank ' + tank_str + ' not found')
        return tank_str


    @classmethod
    def get_tank_user_strs(cls) -> str:
        return cls.tanks["userStr"].keys()


    @classmethod
    def chk_JSON(cls, json_obj, check = None) -> bool:
        try:
            if (check is None): 
                # nothing to check
                return True
            if (check == 'tank_stats'):
                if cls.chk_JSON_tank_stats(json_obj):
                    return True
                else: 
                    logging.debug('Checking tank list JSON failed.')
                    return False
            elif (check == 'player_stats'):
                if cls.chk_JSON_player_stats(json_obj):
                    return True
                else: 
                    logging.debug('Checking player JSON failed.')
                    return False
            elif (check == 'tankopedia'):
                if cls.chk_JSON_tankopedia(json_obj):
                    return True
                else:
                    logging.debug('Checking tank JSON failed.')
                    return False
            elif (check == 'account_id'):
                if cls.chk_JSON_get_account_id(json_obj):
                    return True
                else: 
                    logging.debug('Checking account_id JSON failed.')
                    return False
        except (TypeError, ValueError) as err:
            logging.debug(str(err))
        return False


    @classmethod
    def chk_JSON_status(cls, json_resp: dict) -> bool:
        try:
            if (json_resp is None) or ('status' not in json_resp) or (json_resp['status'] is None):
                return False
            elif (json_resp['status'] == 'ok') and ('data' in json_resp):
                return True
            elif json_resp['status'] == 'error':
                if ('error' in json_resp):
                    error_msg = 'Received an error'
                    if ('message' in json_resp['error']) and (json_resp['error']['message'] is not None):
                        error_msg = error_msg + ': ' +  json_resp['error']['message']
                    if ('value' in json_resp['error']) and (json_resp['error']['value'] is not None):
                        error_msg = error_msg + ' Value: ' + json_resp['error']['value']
                    logging.debug(error_msg)
                return False
            else:
                logging.error('Unknown status-code: ' + json_resp['status'])
                return False
        except KeyError as err:
            logging.error('No field found in JSON data', err)
        except Exception as err:
            logging.error("JSON format error", err)
        return False


    @classmethod
    def chk_JSON_get_account_id(cls, json_resp: dict) -> bool:
        try:
            if cls.chk_JSON_status(json_resp): 
                if (json_resp['meta']['count'] > 0):
                    return True                
        except KeyError as err:
            logging.error('Key not found', err)
        except Exception as err:
            logging.error(str(err))
        return False

    # @classmethod
    # def chkJSONplayer(cls, json_resp: dict) -> bool:
    #     """"Check String for being a valid Player JSON file"""
    #     try:
    #         if cls.chk_JSON_status(json_resp): 
    #             if int(json_resp[0]['account_id']) > 0:
    #                 return True
    #     except KeyError as err:
    #         logging.error('Key not found', err)
    #     except:
    #         logging.debug("JSON check failed")
    #     return False
    
    @classmethod
    def chk_JSON_tankopedia(cls, json_resp: dict) -> bool:
        """"Check String for being a valid Tankopedia JSON file"""
        try:
            if cls.chk_JSON_status(json_resp):
                if int(json_resp[0]['tank_id']) > 0:
                    return True
        except KeyError as err:
            logging.error('Key not found', err)
        except:
            logging.debug("JSON check failed")
        return False
    

    @classmethod    
    def chk_JSON_player_stats(cls, json_resp: dict) -> bool:
        """"Check String for being a valid Tank JSON file"""
        try:
            if cls.chk_JSON_status(json_resp): 
                for acc in json_resp['data']:
                    if json_resp['data'][acc] is not None:
                        return True 
        except KeyError as err:
            logging.error('Key not found', err)
        except:
            logging.debug("JSON check failed")
        return False


    @classmethod
    def chk_JSON_tank_stats(cls, json_resp: dict) -> bool:
        """"Check String for being a valid Tank list JSON file"""
        try:
            if cls.chk_JSON_status(json_resp):
                if ('data' in json_resp) and (len(json_resp['data']) > 0):
                    logging.debug('JSON tank list check OK')
                    return True
        except Exception as err:
            logging.error('JSON check FAILED: ' + str(json_resp) )
            logging.error(str(err))
        return False


    @classmethod
    def chk_last_battle_time(cls, last_battle_time: int, now: Optional[int] = None) -> int:
        """Check that the last_battle_time is not inthe future (MAX_UINT)"""
        if now is None:
            now = int(time.time())
        if last_battle_time > now  + cls.TIME_SYNC_THRESHOLD:
            return now
        else: 
            return last_battle_time


    ## Methods --------------------------------------------------
    def load_tanks(self, tankopedia_fn: str):
        """Load tanks from tankopedia JSON"""
        if tankopedia_fn is None:
            return False 

        try:
            with open(tankopedia_fn, 'rt', encoding='utf8') as f:
                self.tanks = json.loads(f.read())
                self.tanks_by_tier = dict()
                for tier in range(1,11):
                    self.tanks_by_tier[str(tier)] = list()
                for tank in self.tanks['data'].values():
                    self.tanks_by_tier[str(tank['tier'])].append(tank['tank_id'])
                return True
        except Exception as err:
            logging.error('Could not read tankopedia: ' + tankopedia_fn, err) 
        return False     
     

    def get_tanks_by_tier(self, tier: int) -> list:
        """Returns tank_ids by tier"""
        try:
            return self.tanks_by_tier[str(tier)]
        except KeyError as err:
            logging.error('Invalid tier', err)
        return None  
    

    def get_url_clan_info(self, server: str, clan_id: int) -> Optional[str]:
        try:
            if server is None:
                return None 
            return self.URL_WG_SERVER[server] + self.URL_WG_CLAN_INFO + self.WG_app_id + '&clan_id=' + str(clan_id)
        except Exception as err:
            if (server is None) or (server.lower() not in WG.ACCOUNT_ID_SERVER.keys()):
                logging.error('No server name or invalid server name given: ' + server if (server !=  None) else '')
                logging.error('Available servers: ' + ', '.join(WG.ACCOUNT_ID_SERVER.keys()))
            logging.error(str(err))
        return None


    def get_url_player_tank_list(self, account_id: int) -> str:
        return self.get_url_player_tanks_stats(account_id, fields='tank_id')


    def get_url_player_tanks_stats(self, account_id: int, tank_ids: list = [], fields: list = []) -> Optional[str]: 
        server = self.get_server(account_id)
        if server is None:
            return None        
        if (tank_ids is not None) and (len(tank_ids) > 0):
            tank_id_str= '&tank_id=' + '%2C'.join([ str(x) for x in tank_ids])
        else:
            # emtpy tank-id list returns all the player's tanks  
            tank_id_str = ''

        if (fields is not None) and (len(fields) > 0):
            field_str =  '&fields=' + '%2C'.join(fields)
        else:
            # return all the fields
            field_str = ''

        return self.URL_WG_SERVER[server] + self.URL_WG_PLAYER_TANK_STATS + self.WG_app_id + '&account_id=' + str(account_id) + tank_id_str + field_str
        

    def get_url_player_stats(self, account_id,  fields) -> Optional[str]: 
        try:
            server = self.get_server(account_id)
            if server is None:
                return None 
            if (fields is not None) and (len(fields) > 0):
                field_str =  '&fields=' + '%2C'.join(fields)
            else:
                # return all the fields
                field_str = ''

            return self.URL_WG_SERVER[server] + self.URL_WG_PLAYER_STATS + self.WG_app_id + '&account_id=' + str(account_id) + field_str
        except Exception as err:
            if (server is None):
                logging.error('Invalid account_id')
            logging.error(str(err))
        return None


    def get_url_player_achievements(self, account_ids: list,  fields : str = 'max_series') -> Optional[str]: 
        try:
            # assumming that all account_ids are from the same server. This has to be taken care. 
            server = self.get_server(account_ids[0])

            if server is None:
                return None 
            account_ids_str = '%2C'.join(str(id) for id in account_ids)
            if (fields is not None) and (len(fields) > 0):
                field_str =  '&fields=' + '%2C'.join(fields)
            else:
                # return all the fields
                field_str = ''

            return self.URL_WG_SERVER[server] + self.URL_WG_PLAYER_ACHIEVEMENTS + self.WG_app_id + '&account_id=' + account_ids_str + field_str
        except Exception as err:
            if (server is None):
                logging.error('Invalid account_id')
            logging.error(str(err))
        return None


    def get_url_account_id(self, nickname, server) -> Optional[int]:
        try:
            return self.URL_WG_SERVER[server] + self.URL_WG_ACCOUNT_ID + self.WG_app_id + '&search=' + urllib.parse.quote(nickname)
        except Exception as err:
            if nickname is None or len(nickname) == 0:
                logging.error('No nickname given')            
            if (server is None) or (server.lower() not in WG.ACCOUNT_ID_SERVER.keys()):
                logging.error('No server name or invalid server name given: ' + server if (server !=  None) else '')
                logging.error('Available servers: ' + ', '.join(WG.ACCOUNT_ID_SERVER.keys()))
            logging.error(str(err))
        return None


    def url_get_server(self, url: str) -> str: 
        """Decode WG server from the URL"""         
        try:            
            for server in self.session:
                if url.startswith(self.URL_WG_SERVER[server]):
                    return server
        except Exception as err:
            logging.error(str(err))
        return 'eu'  # default


    def print_request_stats(self):
        """Print session statics"""
        if self.global_rate_limit:
            logging.warning('Globar rate limit: ' + self.session.get_stats_str())
        else:
            for server in self.session:
                logging.warning('Per server rate limits: '  + server + ': '+ self.session[server].get_stats_str())


    async def get_url_JSON(self, url: str, chk_JSON_func = None, max_tries = MAX_RETRIES) -> dict:
        """Class WG get_url_JSON() for load balancing between WG servers 
        that have individial rate limits"""
        
        server = self.url_get_server(url)
        session = self.session[server]
        logging.debug('server:' + server)
        return await get_url_JSON(session, url, chk_JSON_func, max_tries)


    async def get_account_id(self, nickname: str) -> int:
        """Get WG account_id for a nickname"""
        try:
            nick    = None
            server  = None
            nick, server = nickname.split('@')
            logging.debug(nick + ' @ '+ server)
            server = server.lower()
            if nick is None or server is None:
                raise ValueError('Invalid nickname given: ' + nickname)
            url = self.get_url_account_id(nick, server)

            json_data = await self.get_url_JSON(url, self.chk_JSON_status)
            for res in json_data['data']:
                if res['nickname'].lower() == nick.lower(): 
                    return res['account_id']
            logging.error('No WG account_id found: ' + nickname)
            
        except Exception as err:
            logging.error(str(err))
        return None
      

    async def get_player_tank_stats(self, account_id: int, tank_ids = [], fields = [], cache=True, cache_only = False) -> dict:
        """Get player's stats (WR, # of battles) in a tank or all tanks (empty tank_ids[])"""
        try:
            stats = None

            # try cached stats first:
            if cache:
                stats = await self.get_cached_tank_stats(account_id, tank_ids, fields)
                if stats is not None:
                    return stats
                if cache_only: 
                    return None

            # Cached stats not found, fetching new ones
            url = self.get_url_player_tanks_stats(account_id, tank_ids, fields)
            json_data = await self.get_url_JSON(url, self.chk_JSON_status)
            if json_data is not None:
                #logging.debug('JSON Response received: ' + str(json_data))
                stats = json_data['data'][str(account_id)]
                if cache:
                    await self.put_2_statsQ('tank_stats', [account_id, tank_ids], stats)
                return stats
        except Exception as err:
            logging.error(str(err))
        return None

   
    async def get_player_stats(self, account_id: int, fields = [], cache=True, cache_only = False) -> dict:
        """Get player's global stats """
        try:
            #logging.debug('account_id: ' + str(account_id) )
            stats = None

            # try cached stats first:
            if cache:
                stats = await self.get_cached_player_stats(account_id,fields)
                # stats found unless StatsNotFound exception is raised 
                return stats

        except StatsNotFound as err:
            if cache_only: 
               return None
            
            # No cached stats found, need to retrieve
            logging.debug(str(err))
            pass
        
        try:
            # Cached stats not found, fetching new ones
            url = self.get_url_player_stats(account_id, fields)
            json_data = await self.get_url_JSON(url, self.chk_JSON_status)
            if json_data is not None:
                #logging.debug('JSON Response received: ' + str(json_data))
                stats = json_data['data'][str(account_id)]
                if cache:
                    await self.put_2_statsQ('player_stats', [account_id], stats)
                return stats
        except Exception as err:
            logging.error(str(err))
        return None


    async def get_player_achievements(self, account_ids: list, fields = [], cache=True) -> dict:
        """Get player's achievements stats """
        try:
            account_ids = set(account_ids)
            stats = dict()
            if len(account_ids) == 0:
                logging.debug('Zero account_ids given')
                return None

            # try cached stats first:
            if cache:
                logging.debug('Checking for cached stats')
                account_ids_cached = set()
                for account_id in account_ids:
                    try:
                        stats[str(account_id)] = await self.get_cached_player_achievements(account_id,fields)
                        account_ids_cached.add(account_id)
                    except StatsNotFound as err:
                        # No cached stats found, need to retrieve
                        logging.debug(str(err))                
                account_ids = account_ids.difference(account_ids_cached)
                if len(account_ids) == 0:
                    return stats
            logging.debug('fetching new stats')
            # Cached stats not found, fetching new ones
            url = self.get_url_player_achievements(list(account_ids), fields)
            json_data = await self.get_url_JSON(url, self.chk_JSON_status)
            if (json_data is not None) and ('data' in json_data):
                #logging.debug('JSON Response received: ' + str(json_data))
                for account_id in json_data['data'].keys():
                    stats[account_id] = json_data['data'][account_id]
                    if cache:
                        await self.put_2_statsQ('player_achievements', [int(account_id)], json_data['data'][account_id])
                return stats
        except Exception as err:
            logging.error(str(err))
        return None


    def merge_player_stats(self, stats1: dict, stats2: dict) -> dict:
        try:
            if stats2 is None: return stats1								
            for keyA in stats2:
                if keyA not in stats1:
                    stats1[keyA] = stats2[keyA]
                else:
                    for keyB in stats2[keyA]:
                        stats1[keyA][keyB] = stats2[keyA][keyB] 
            return stats1
        except KeyError as err:
            logging.error('Key not found', err) 
        return None


    def get_tank_data(self, tank_id: int, field: str):
        if self.tanks is None:
            return None
        try:
            return self.tanks['data'][str(tank_id)][field]
        except KeyError as err:
            logging.error('Key not found', err)
        return None

 
    def get_tank_tier(self, tank_id: int):
        return self.get_tank_data(tank_id, 'tier')


    def get_tank_name_id(self, tank_id: int):
        return self.get_tank_data(tank_id, 'name')


    async def put_2_statsQ(self, statsType: str, key: list, stats: list):
        """Save stats to a async queue to be saved by the stat_saver -task"""
        if self.statsQ is None:
            return False
        else:
            await self.statsQ.put([ statsType, key, stats, NOW() ])
            return True


    async def stat_saver(self): 
        """Async task for saving stats into cache in background"""

        if self.statsQ is None:
            logging.error('No statsQ defined')
            return None
        try:
            self.cache = await aiosqlite.connect(WG.CACHE_DB_FILE)
            ## Create cache tables table
            await self.cache.execute(WG.SQL_TANK_STATS_CREATE_TBL)
            await self.cache.execute(WG.SQL_PLAYER_STATS_CREATE_TBL)
            await self.cache.execute(WG.SQL_PLAYER_ACHIEVEMENTS_CREATE_TBL)

            await self.cache.commit()
            
            async with self.cache.execute(WG.SQL_TANK_STATS_COUNT) as cursor:
                logging.debug('Cache contains: ' + str((await cursor.fetchone())[0]) + ' cached player tank stat records' )
        except Exception as err:
            logging.error(str(err))
            sys.exit(1)

        while True:
            try:
                stats = await self.statsQ.get()
            
                stats_type  = stats[0]
                key         = stats[1]
                stats_data  = stats[2]
                update_time = stats[3]

                if stats_type == 'tank_stats':
                    await self.store_tank_stats(key, stats_data, update_time)
                elif stats_type == 'player_stats':
                    await self.store_player_stats(key, stats_data, update_time)
                elif stats_type == 'player_achievements':
                    await self.store_player_achievements(key, stats_data, update_time)
                else: 
                    logging.error('Function to saves stats type \'' + stats_type + '\' is not implemented yet')
            
            except (asyncio.CancelledError):
                # this is an eternal loop that will wait until cancelled	
                return None

            except Exception as err:
                logging.error(str(err))
            self.statsQ.task_done()
        return None


    async def cleanup_cache(self, grace_time = CACHE_GRACE_TIME):
        """Clean old cache records"""
        if self.cache is None:
            logging.debug('No active cache')
            return None
        for table in WG.SQL_TABLES:
            async with self.cache.execute(WG.SQL_CHECK_TABLE_EXITS, (table,)) as cursor:
                if (await cursor.fetchone()) is not None:
                    logging.debug('Pruning cache table: ' + table)
                    await self.cache.execute(WG.SQL_PRUNE_CACHE.format(table, NOW() - grace_time))
                    await self.cache.commit()
        return None


    async def store_tank_stats(self, key: list , stats_data: list, update_time: int):
        """Save tank stats into cache"""
        try:
            account_id  = key[0]
            tank_ids    = set(key[1])
            if stats_data is not None:
                for stat in stats_data:
                    tank_id = stat['tank_id']
                    await self.cache.execute(WG.SQL_TANK_STATS_UPDATE, (account_id, tank_id, update_time, json.dumps(stat)))
                    tank_ids.remove(tank_id)
            # no stats found => Add None to mark that
            for tank_id in tank_ids:
                await self.cache.execute(WG.SQL_TANK_STATS_UPDATE, (account_id, tank_id, update_time, None))
            await self.cache.commit()
            logging.debug('Cached tank stats saved for account_id: ' + str(account_id) )
            return True
        except Exception as err:
            logging.error(str(err))
            return False


    async def store_player_stats(self, key: list , stats_data: list, update_time: int) -> bool:
        """Save player stats into cache"""
        try:
            account_id  = key[0]
            if stats_data is not None:
                await self.cache.execute(WG.SQL_PLAYER_STATS_UPDATE, (account_id, update_time, json.dumps(stats_data)))
            else:
                await self.cache.execute(WG.SQL_PLAYER_STATS_UPDATE, (account_id, update_time, None))
            await self.cache.commit()
            logging.debug('Cached player stats saved for account_id: ' + str(account_id) )
            return True
        except Exception as err:
            logging.error(str(err))
            return False


    async def store_player_achievements(self, key: list , stats_data: list, update_time: int):
        """Save player stats into cache"""
        try:
            account_id  = key[0]
            if stats_data is not None:
                await self.cache.execute(WG.SQL_PLAYER_ACHIEVEMENTS_UPDATE, (account_id, update_time, json.dumps(stats_data)))
            else:
                await self.cache.execute(WG.SQL_PLAYER_ACHIEVEMENTS_UPDATE, (account_id, update_time, None))
            await self.cache.commit()
            logging.debug('Cached player achievements saved for account_id: ' + str(account_id) )
            return True
        except Exception as err:
            logging.error(str(err))
            return False


    async def get_cached_tank_stats(self, account_id: int, tank_ids: list, fields: list ):
        try:
            # test for cacheDB existence
            logging.debug('Trying cached stats first')
            if self.cache is None:
                logging.debug('No cache DB')
                return None
            
            stats = []
            if len(tank_ids) > 0:
                sql_query = 'SELECT * FROM ' +  WG.SQL_TANK_STATS_TBL + ' WHERE account_id = ? AND update_time > ? AND tank_id IN (' + ','.join([str(x) for x in tank_ids]) + ')'
            else:
                sql_query = 'SELECT * FROM ' +  WG.SQL_TANK_STATS_TBL + ' WHERE account_id = ? AND update_time > ?'

            async with self.cache.execute(sql_query, [account_id, int(time.time()) - WG.CACHE_GRACE_TIME] ) as cursor:
                tank_ids = set(tank_ids)
                async for row in cursor:
                    #logging.debug('account_id: ' + str(account_id) + ': 1')
                    if row[3] is None:
                        # None/null stats found in cache 
                        # i.e. stats have been requested, but not returned from WG API
                        tank_ids.remove(row[1])
                        continue
                    #logging.debug('account_id: ' + str(account_id) + ': 2')
                    stats.append(json.loads(row[3]))
                    # logging.debug('account_id: ' + str(account_id) + ': 3')
                    tank_ids.remove(row[1])
                
                # return stats ONLY if ALL the requested stats were found in cache
                if tank_ids == set():
                    logging.debug('Cached stats found: ' + str(account_id))
                    return stats
           
        except Exception as err:
            logging.error(str(err))
        logging.debug('No cached stats found')
        return None


    async def get_cached_player_stats(self, account_id, fields):
        try:
            # test for cacheDB existence
            logging.debug('Trying cached stats first')
            if self.cache is None:
                #logging.debug('No cache DB')
                raise StatsNotFound('No cache DB in use')
                      
            async with self.cache.execute(WG.SQL_PLAYER_STATS_CACHED, [account_id, NOW() - WG.CACHE_GRACE_TIME] ) as cursor:
                row = await cursor.fetchone()
                #logging.debug('account_id: ' + str(account_id) + ': 1')
                if row is None:
                    # no cached stats found, marked with an empty array
                    #logging.debug('No cached stats found')
                    raise StatsNotFound('No cached stats found')
                
                logging.debug('Cached stats found')    
                if row[2] is None:
                    # None/null stats found in cache 
                    # i.e. stats have been requested, but not returned from WG API
                    return None
                else:
                    # Return proper stats 
                    return json.loads(row[2])
        except StatsNotFound as err:
            logging.debug(str(err))
            raise
        except Exception as err:
            logging.error('Error trying to look for cached stats', str(err))
        return None


    async def get_cached_player_achievements(self, account_id, fields):
        try:
            # test for cacheDB existence
            logging.debug('Trying cached stats first')
            if self.cache is None:
                #logging.debug('No cache DB')
                raise StatsNotFound('No cache DB in use')
                      
            async with self.cache.execute(WG.SQL_PLAYER_ACHIEVEMENTS_CACHED, [account_id, NOW() - WG.CACHE_GRACE_TIME] ) as cursor:
                row = await cursor.fetchone()
                #logging.debug('account_id: ' + str(account_id) + ': 1')
                if row is None:
                    # no cached stats found, marked with an empty array
                    #logging.debug('No cached stats found')
                    raise StatsNotFound('No cached stats found')
                
                logging.debug('Cached stats found')    
                if row[2] is None:
                    # None/null stats found in cache 
                    # i.e. stats have been requested, but not returned from WG API
                    return None
                else:
                    # Return proper stats 
                    return json.loads(row[2])
        except StatsNotFound as err:
            logging.debug(str(err))
            raise
        except Exception as err:
            logging.error('Error trying to look for cached stats', str(err))
        return None
