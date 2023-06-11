import sys
import pytest  # type: ignore
from os.path import dirname, realpath, join as pjoin, basename
from pathlib import Path
import logging

logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug

sys.path.insert(0, str(Path(__file__).parent.parent.resolve() / "src"))

from blitzutils import Account, Region, WGApi
from blitzutils import WGAccountInfo, WGPlayerAchievementsMaxSeries, WGTankStat


########################################################
#
# Test Plan
#
########################################################

# Test retrieval and parsing of:
# 1) AccountInfo API
# 2) TankStats API
# 3) Player achivements API

########################################################
#
# Fixtures
#
########################################################

FIXTURE_DIR = Path(dirname(realpath(__file__)))
ACCOUNTS = pytest.mark.datafiles(
    FIXTURE_DIR / "04_Accounts_EU.csv", FIXTURE_DIR / "04_Accounts_Com.csv", FIXTURE_DIR / "04_Accounts_Asia.csv"
)


@pytest.mark.asyncio
@pytest.fixture
@ACCOUNTS
async def accounts(datafiles: Path) -> dict[Region, list[Account]]:
    res: dict[Region, list[Account]] = dict()
    for account_fn in datafiles.iterdir():
        region_accounts: list[Account] = list()
        async for account in Account.import_file(str(account_fn.resolve())):
            region_accounts.append(account)

        region: Region = region_accounts[0].region
        res[region] = region_accounts
    return res


@pytest.fixture
def accounts_per_region() -> int:
    return 50  # number of tanks in the 01_Tankopedia.json


########################################################
#
# Tests
#
########################################################


@pytest.mark.asyncio
@ACCOUNTS
async def test_1_api_account_info(datafiles: Path) -> None:
    wg: WGApi = WGApi()
    for account_fn in datafiles.iterdir():
        accounts: list[Account] = list()
        async for account in Account.import_file(str(account_fn.resolve())):
            accounts.append(account)

        region: Region = accounts[0].region

        account_ids: list[int] = list()
        for account in accounts:
            account_ids.append(account.id)

        account_infos = await wg.get_account_info(account_ids=account_ids, region=region)
        assert account_infos is not None, f"could no retrieve account infos for {region}"
        assert len(account_infos) > 0, f"could no retrieve any account infos for {region}"
        assert type(account_infos[0]) is WGAccountInfo, "incorrect type returned"
    await wg.close()


@pytest.mark.asyncio
@ACCOUNTS
async def test_2_api_tank_stats(datafiles: Path) -> None:
    wg: WGApi = WGApi()
    for account_fn in datafiles.iterdir():
        accounts: list[Account] = list()
        async for account in Account.import_file(str(account_fn.resolve())):
            accounts.append(account)

        region: Region = accounts[0].region

        account_ids: list[int] = list()
        stats_ok: bool = False
        for account in accounts[:10]:
            tank_stats = await wg.get_tank_stats(account_id=account.id, region=region)
            if tank_stats is None:
                debug(f"account_id={account} ({region}) did not return tank stats")
                continue
            stats_ok = True
            assert len(tank_stats) > 0, f"no tanks stats found for account_id={account}"
            assert type(tank_stats[0]) is WGTankStat, "incorrect type returned"

        assert stats_ok, f"Could not find any stats for {region} region"
    await wg.close()


@pytest.mark.asyncio
@ACCOUNTS
async def test_3_api_player_achievements(datafiles: Path) -> None:
    wg: WGApi = WGApi()
    for account_fn in datafiles.iterdir():
        accounts: list[Account] = list()
        async for account in Account.import_file(str(account_fn.resolve())):
            accounts.append(account)

        region: Region = accounts[0].region

        account_ids: list[int] = list()
        for account in accounts:
            account_ids.append(account.id)

        pams = await wg.get_player_achievements(account_ids=account_ids, region=region)
        assert pams is not None, f"could no retrieve account infos for {region}"
        assert len(pams) > 0, f"could no retrieve any account infos for {region}"
        assert type(pams[0]) is WGPlayerAchievementsMaxSeries, "incorrect type returned"
    await wg.close()
