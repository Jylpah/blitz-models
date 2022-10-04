## -----------------------------------------------------------
#### Utils
#
## -----------------------------------------------------------

import os
import aiofiles, aiohttp
import sys
import json
import logging
from typing import Optional, Callable, Union, Any, Dict


async def save_JSON(filename: str, json_data: dict, sort_keys : bool = False, pretty : bool = True) -> bool:
    """Save JSON data into file"""
    try:        
        dirname = os.path.dirname(filename)
        if (dirname != '') and not os.path.isdir(dirname):
            os.makedirs(dirname, 0o770-os.umask(0))
        async with aiofiles.open(filename,'w', encoding="utf8") as outfile:
            if pretty:
                await outfile.write(json.dumps(json_data, ensure_ascii=False, indent=4, sort_keys=sort_keys))
            else:
                await outfile.write(json.dumps(json_data, ensure_ascii=False, sort_keys=sort_keys))
            return True
    except Exception as err:
        logging.error('Error saving JSON', err)
    return False


async def open_JSON(filename: str, chk_JSON_func : Optional[Callable[object, bool]] = None) -> Optional[dict]:
    try:
        async with aiofiles.open(filename) as fp:
            json_data : Optional[Any] = json.loads(await fp.read())
            if (chk_JSON_func is None):
                logging.debug("JSON file content not checked: " + filename)
                return json_data                
            elif chk_JSON_func(json_data):
                logging.debug("JSON File is valid: " + filename)
                return json_data
            else:
                logging.debug('JSON File has invalid content: ' + filename)
    except Exception as err:
        error('Unexpected error when reading file: ' + filename, err)
    return None


async def get_url_JSON(session: aiohttp.ClientSession, url: str, chk_JSON_func = None, max_tries = MAX_RETRIES) -> dict:
        """Retrieve (GET) an URL and return JSON object"""
        if session == None:
            logging.error('Session must be initialized first')
            sys.exit(1)
        if url == None:
            logging.error('url=None parameter given')
            return None
        
        ## To avoid excessive use of servers            
        for retry in range(1,max_tries+1):
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:                        
                        logging.debug('HTTP request OK')
                        json_resp = await resp.json()
                        if json_resp["status"] == "ok":
                            if (chk_JSON_func == None) or chk_JSON_func(json_resp):
                                # debug("Received valid JSON: " + str(json_resp))
                                return json_resp
                        else:
                            wg_error = json_resp["error"]
                            keys = ['message', 'field', 'value']
                            logging.error("WG API Error: " + str(wg_error["code"]) + ': ' + [ wg_error.get(key) for key in keys ].join(' : ') )
                        # Sometimes WG API returns JSON error even a retry gives valid JSON
                   # elif resp.status == 407:
                   #     error('WG API returned 407: ' + json_resp['error']['message'])
                    else:
                        logging.error('WG API returned HTTP error ' + str(resp.status))
                        
                    if retry == max_tries:                        
                        break
                    logging.debug('Retrying URL [' + str(retry) + '/' +  str(max_tries) + ']: ' + url )
                await asyncio.sleep(SLEEP)    

            except aiohttp.ClientError as err:
                logging.debug("Could not retrieve URL: " + url, exception=err)
            except asyncio.CancelledError as err:
                logging.debug('Queue gets cancelled while still working.', exception=err)
                break
            except Exception as err:
                logging.debug('Unexpected Exception', exception=err)
        logging.debug("Could not retrieve URL: " + url)
        return None