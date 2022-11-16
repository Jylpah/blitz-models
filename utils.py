## -----------------------------------------------------------
#### Utils
#
## -----------------------------------------------------------

import os
import aiofiles
import aiohttp
import asyncio
import json
import logging
from typing import Optional, List, Callable, Union, Any, Dict, Tuple

logger 	= logging.getLogger()
error 	= logger.error
verbose_std	= logger.warning
verbose	= logger.info
debug	= logger.debug

JsonType = Union[int, str, bool, List, Dict]
JsonFunc = Callable[..., Tuple[bool, str]]
MAX_RETRIES : int = 3
SLEEP       : float = 3

async def save_JSON(filename: str, json_data: JsonType, sort_keys : bool = False, pretty : bool = True) -> bool:
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
		error('Error saving JSON', err)
	return False


async def open_JSON(filename: str, chk_JSON_func : Optional[JsonFunc] = None) -> Optional[Any]:
	try:
		async with aiofiles.open(filename) as fp:
			json_data : Optional[Any] = json.loads(await fp.read())
			if (chk_JSON_func is None):
				debug("JSON file content not checked: " + filename)
				return json_data                
			elif chk_JSON_func(json_data):
				debug("JSON File is valid: " + filename)
				return json_data
			else:
				debug('JSON File has invalid content: ' + filename)
	except Exception as err:
		error('Unexpected error when reading file: ' + filename, err)
	return None


async def get_url_JSON(session: aiohttp.ClientSession, url: str, 
						chk_JSON_func : Optional[JsonFunc] = None, 
						max_tries : int = MAX_RETRIES) -> Optional[Any]:
		"""Retrieve (GET) an URL and return JSON object"""

		assert session is not None, 'Session must be initialized first'
		assert url is not None, 'url cannot be None'
		assert MAX_RETRIES is not None, 'MAX_RETRIES cannot be None'

		for retry in range(1,max_tries+1):
			try:
				async with session.get(url) as resp:
					if resp.status == 200:                        
						debug('HTTP request OK')
						json_resp = await resp.json()
						if json_resp is not None:
							if chk_JSON_func is None:
								debug("Not testing JSON content: chk_JSON_func is not defined")
								return json_resp
							json_ok, json_error = chk_JSON_func(json_resp)
							if json_ok:
								if logger.level == logging.DEBUG:
									debug(f'{url}: ')
									debug(str(json_resp))
								return json_resp
							else:
								error(json_error)                         
						else:
							error(f"API returned None: {url}")
					else:
						error(f'HTTP error {str(resp.status)}')
					if retry == max_tries:                        
						break
					debug(f'Retrying URL [ {str(retry)}/{str(max_tries)} ]: {url}' )
				await asyncio.sleep(SLEEP)    

			except aiohttp.ClientError as err:
				debug(f"Could not retrieve URL: {url} : {str(err)}")
			except asyncio.CancelledError as err:
				debug(f'Queue gets cancelled while still working: {str(err)}')
				break
			except Exception as err:
				debug(f'Unexpected Exception {str(err)}')
		debug("Could not retrieve URL: " + url)
		return None

# json_error = json_resp["error"]
# keys = ['message', 'field', 'value']
# error(f"API Error: {str(json_error['code'])} : {' : '.join([json_error.get(key) for key in keys ])}" )
# Sometimes WG API returns JSON error even a retry gives valid JSON