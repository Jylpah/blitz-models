## -----------------------------------------------------------
#### Class WoTinspector 
# 
# replays.wotinspector.com
## -----------------------------------------------------------

from typing import Optional, Union
import logging, aiohttp, json, re, sys, urllib, asyncio
from bs4 import BeautifulSoup                                      # type: ignore
from pyutils.throttledclientsession import ThrottledClientSession

class WoTinspector:
    URL_WI          : str = 'https://replays.wotinspector.com'
    URL_REPLAY_LIST : str = URL_WI + '/en/sort/ut/page/'
    URL_REPLAY_DL   : str = URL_WI + '/en/download/'  
    URL_REPLAY_VIEW : str = URL_WI +'/en/view/'
    URL_REPLAY_UL   : str = 'https://api.wotinspector.com/replay/upload?'
    URL_REPLAY_INFO : str = 'https://api.wotinspector.com/replay/upload?details=full&key='
    URL_TANK_DB     : str = "https://wotinspector.com/static/armorinspector/tank_db_blitz.js"

    REPLAY_N = 1
    DEFAULT_RATE_LIMIT = 20/3600  # 20 requests / hour

    def __init__(self, rate_limit: float = DEFAULT_RATE_LIMIT, auth_token: Optional[str] = None):

        headers : Optional[dict[str, str]] = None
        if auth_token is not None:
            headers = dict()
            headers['Authentication'] = 'Token ' + auth_token

        self.session = ThrottledClientSession(rate_limit=rate_limit, filters=[self.URL_REPLAY_DL, self.URL_REPLAY_LIST], 
                                                re_filter=False, limit_filtered=True, headers = headers)


    async def close(self):
        if self.session != None:
            logging.debug('Closing aiohttp session')
            await self.session.close()
       

    async def get_tankopedia(self, filename = 'tanks.json'):
        """Retrieve Tankpedia from WoTinspector.com"""
    
        async with self.session.get(self.URL_TANK_DB) as r:
            if r.status == 200:
                WI_tank_db=await r.text()
                WI_tank_db = WI_tank_db.split("\n")
            else:
                print('Error: Could not get valid HTTPS response. HTTP: ' + str(r.status) )  
                sys.exit(1) 
            tanks = {}
            n = 0
            p = re.compile('\\s*(\\d+):\\s{"en":"([^"]+)",.*?"tier":(\\d+), "type":(\\d), "premium":(\\d).*')
            for line in WI_tank_db[1:-1]:
                try:
                    m = p.match(line)
                    tank = {}
                    tank['tank_id'] = int(m.group(1))
                    tank['name'] = m.group(2)
                    tank['tier'] = int(m.group(3))
                    tank['type'] = WG.TANK_TYPE[int(m.group(4))]
                    tank['is_premium'] = (int(m.group(5)) == 1)
                    tanks[str(m.group(1))] = tank
                    n += 1
                except Exception as err:
                    logging.error(str(err))
            
            tankopedia = {}
            tankopedia['status'] = "ok"
            tankopedia['meta'] = {"count" : n}
            tankopedia['data'] = tanks
            
            logging.warning("Tankopedia has " + str(n) + " tanks in: " + filename)
            with open(filename,'w') as outfile:
                outfile.write(json.dumps(tankopedia, ensure_ascii=False, indent=4, sort_keys=False))
            return None


    async def get_replay_JSON(self, replay_id: str):
        json_resp = await get_url_JSON(self.session, self.URL_REPLAY_INFO + replay_id, chk_JSON_func=None)
        try:
            if self.chk_JSON_replay(json_resp):
                return json_resp
            else:
                return None
        except Exception as err:
            logging.error('Unexpected Exception', err) 
            return None


    async def post_replay(self,  data, filename = 'Replay', account_id = 0, title = 'Replay', priv = False, N = None):
        try:
            N = N if N != None else self.REPLAY_N
            self.REPLAY_N += 1

            hash = hashlib.md5()
            hash.update(data)
            replay_id = hash.hexdigest()

            ##  Testing if the replay has already been posted
            json_resp = await self.get_replay_JSON(replay_id)
            if json_resp != None:
                logging.debug('Already uploaded: ' + title, id=N)
                return json_resp

            params = {
                'title'			: title,
                'private' 		: (1 if priv else 0),
                'uploaded_by'	: account_id,
                'details'		: 'full',
                'key'           : replay_id
            } 

            url = self.URL_REPLAY_UL + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
            #debug('URL: ' + url)
            headers ={'Content-type':  'application/x-www-form-urlencoded'}
            payload = { 'file' : (filename, base64.b64encode(data)) }
        except Exception as err:
            logging.error('Unexpected Exception', exception=err, id=N)
            return None

        json_resp  = None
        for retry in range(MAX_RETRIES):
            logging.debug('Posting: ' + title + ' Try #: ' + str(retry + 1) + '/' + str(MAX_RETRIES), id=N )
            try:
                async with self.session.post(url, headers=headers, data=payload) as resp:
                    logging.debug('HTTP response: '+ str(resp.status), id=N)
                    if resp.status == 200:								
                        logging.debug('HTTP POST 200 = Success. Reading response data', id=N)
                        json_resp = await resp.json()
                        if self.chk_JSON_replay(json_resp):
                            logging.debug('Response data read. Status OK', id=N) 
                            return json_resp	
                        logging.debug(title + ' : Receive invalid JSON', id=N)
                    else:
                        logging.debug('Got HTTP/' + str(resp.status), id=N)
            except Exception as err:
                logging.debug(exception=err, id=N)
            await asyncio.sleep(SLEEP)
            
        logging.debug(' Could not post replay: ' + title, id=N)
        return json_resp


    async def get_replay_listing(self, page: int = 0) -> aiohttp.ClientResponse:
        url = self.get_url_replay_listing(page)
        return await self.session.get(url)


    @classmethod
    def get_url_replay_listing(cls, page : int):
        return cls.URL_REPLAY_LIST + str(page) + '?vt=#filters'


    @classmethod
    def get_url_replay_view(cls, replay_id):
        return cls.URL_REPLAY_VIEW + replay_id


    @classmethod
    def get_replay_links(cls, doc: str):
        """Get replay download links from WoTinspector.com replay listing page"""
        try:
            soup = BeautifulSoup(doc, 'lxml')
            links = soup.find_all('a')
            replay_links = set()
            for tag in links:
                link = tag.get('href',None)
                if (link is not None) and link.startswith(cls.URL_REPLAY_DL):
                    replay_links.add(link)
                    logging.debug('Adding replay link:' + link)
        except Exception as err:
            logging.error(exception=err)
        return replay_links
    

    @classmethod
    def get_replay_id(cls, url):
        return url.rsplit('/', 1)[-1]


    @classmethod
    def chk_JSON_replay(cls, json_resp) -> bool:
        """"Check String for being a valid JSON file"""
        try:
            if ('status' in json_resp) and json_resp['status'] == 'ok' and \
                (get_JSON_value(json_resp, key='data.summary.exp_base') != None) :
                logging.debug("JSON check OK")
                return True 
        except KeyError as err:
            logging.debug('Replay JSON check failed', exception=err)
        except:
            logging.debug("Replay JSON check failed: " + str(json_resp))
        return False