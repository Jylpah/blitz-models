import pytest  # type: ignore
from pathlib import Path
import logging
import json

from blitzmodels import Account, Region, WGApi, AccountInfo
from blitzmodels import (
    PlayerAchievementsMaxSeries,
    TankStat,
    WGApiWoTBlitzTankopedia,
    Tank,
    WGApiTankString,
)

logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug

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

FIXTURE_DIR = Path(__file__).parent
ACCOUNTS = pytest.mark.datafiles(
    FIXTURE_DIR / "04_Accounts_EU.csv",
    FIXTURE_DIR / "04_Accounts_Com.csv",
    FIXTURE_DIR / "04_Accounts_Asia.csv",
    on_duplicate="overwrite",
)


WGAPI_TANKSTR = pytest.mark.datafiles(
    FIXTURE_DIR / "06_WGApiTankString.json", on_duplicate="overwrite"
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


# @pytest.fixture
# @WGAPI_TANKSTR
# def wgapi_tankstrs(datafiles: Path) -> list[WGApiTankString]:
#     res: list[WGApiTankString] = list()
#     for fn in datafiles.iterdir():
#         res.append(WGApiTankString.parse_file(fn))
#     return res


@pytest.fixture
def wgapi_tankstrs_user_strings() -> list[str]:
    return [
        "Oth38_50TP_Tyszkiewicza_S1",
        "A104_M4A3E8A",
        "M6E2V2_BP",
        "F34_ARL_V39_BP",
        "S17_EMIL_1952E2",
        "GB92_FV217",
    ]


# @pytest.fixture
# def accounts_per_region() -> int:
#     return 50  # number of tanks in the 01_Tankopedia.json


@pytest.fixture
def tanks_remove() -> list[int]:
    return [1, 17, 33, 49, 513]


@pytest.fixture
def tanks_updated() -> list[Tank]:
    objs = json.loads(
        """[
        {
            "tank_id": 2129,
            "name": "Crusader",
            "code": "GB20_Crusader",
            "nation": 4,
            "type": "lightTank",
            "tier": 5,
            "is_premium": false
        },
        {
            "tank_id": 5393,
            "name": "VK 16.02 Leopard",
            "code": "VK1602",
            "nation": 1,
            "type": "lightTank",
            "tier": 6,
            "is_premium": false
        },
        {
            "tank_id": 8817,
            "name": "Titan Mk. I",
            "code": "Oth29_A15HW",
            "nation": 7,
            "type": "mediumTank",
            "tier": 5,
            "is_premium": true
        },
        {
            "tank_id": 53585,
            "name": "Matilda Black Prince",
            "code": "GB68_Matilda_Black_Prince",
            "nation": 5,
            "type": "mediumTank",
            "tier": 5,
            "is_premium": false
        },
        {
            "tank_id": 14145,
            "name": "AMX ELC bis bis",
            "code": "ELC_AMX",
            "nation": 4,
            "type": "lightTank",
            "tier": 5,
            "is_premium": false
        }
    ]"""
    )
    tanks: list[Tank] = list()
    for obj in objs:
        tanks.append(Tank.model_validate(obj))
    return tanks


########################################################
#
# Tests
#
########################################################


@pytest.mark.asyncio
@ACCOUNTS
async def test_1_api_account_info(datafiles: Path) -> None:
    async with WGApi() as wg:
        for account_fn in datafiles.iterdir():
            accounts: list[Account] = list()
            async for account in Account.import_file(str(account_fn.resolve())):
                accounts.append(account)

            region: Region = accounts[0].region

            account_ids: list[int] = list()
            for account in accounts:
                account_ids.append(account.id)

            account_infos = await wg.get_account_info(
                account_ids=account_ids, region=region
            )
            assert (
                account_infos is not None
            ), f"could no retrieve account infos for {region}"
            assert (
                len(account_infos) > 0
            ), f"could no retrieve any account infos for {region}"
            assert type(account_infos[0]) is AccountInfo, "incorrect type returned"


@pytest.mark.asyncio
@ACCOUNTS
async def test_2_api_tank_stats(datafiles: Path) -> None:
    async with WGApi() as wg:
        for account_fn in datafiles.iterdir():
            accounts: list[Account] = list()
            async for account in Account.import_file(account_fn):
                accounts.append(account)

            region: Region = accounts[0].region

            stats_ok: bool = False
            for account in accounts[:20]:
                tank_stats = await wg.get_tank_stats(
                    account_id=account.id, region=region
                )
                if tank_stats is None:
                    debug(f"account_id={account} ({region}) did not return tank stats")
                    continue
                stats_ok = True
                assert (
                    len(tank_stats) > 0
                ), f"no tanks stats found for account_id={account}"
                assert type(tank_stats[0]) is TankStat, "incorrect type returned"

            assert stats_ok, f"Could not find any stats for {region} region"


def test_3_tankstat_example_instance() -> None:
    try:
        _ = TankStat.example_instance()
    except Exception as err:
        assert (
            False
        ), f"Could not validate TankStat example instance : {type(err)}: {err}"


@pytest.mark.asyncio
@ACCOUNTS
async def test_4_api_player_achievements(datafiles: Path) -> None:
    async with WGApi() as wg:
        for account_fn in datafiles.iterdir():
            accounts: list[Account] = list()
            async for account in Account.import_file(account_fn):
                accounts.append(account)

            region: Region = accounts[0].region

            account_ids: list[int] = list()
            for account in accounts:
                account_ids.append(account.id)

            pams = await wg.get_player_achievements(
                account_ids=account_ids, region=region
            )
            assert pams is not None, f"could no retrieve account infos for {region}"
            assert len(pams) > 0, f"could no retrieve any account infos for {region}"
            assert (
                type(pams[0]) is PlayerAchievementsMaxSeries
            ), "incorrect type returned"


def test_5_player_achievements_example_instance() -> None:
    try:
        _ = PlayerAchievementsMaxSeries.example_instance()
    except Exception as err:
        assert (
            False
        ), f"Could not validate PlayerAchievementsMaxSeries example instance: {type(err)}: {err}"


@pytest.mark.asyncio
@ACCOUNTS
async def test_6_api_tankopedia(
    datafiles: Path, tanks_remove: list[int], tanks_updated: list[Tank]
) -> None:
    tankopedia: WGApiWoTBlitzTankopedia | None
    async with WGApi() as wg:
        for region in Region.API_regions():
            assert (
                tankopedia := await wg.get_tankopedia(region=region)
            ) is not None, f"could not fetch tankopedia for {region} server"
            assert len(tankopedia) > 0, "API returned empty tankopedia"

        assert (
            tankopedia := await wg.get_tankopedia()
        ) is not None, (
            "could not fetch tankopedia from WG API from (default server = eu)"
        )
        for tank_id in tanks_remove:
            tankopedia.pop(tank_id)

        assert (
            tankopedia_new := await wg.get_tankopedia()
        ) is not None, "could not fetch tankopedia from WG API (default server = eu)"

        for wgtank in tanks_updated:
            tankopedia_new.add(wgtank)

        (added, updated) = tankopedia.update(tankopedia_new)

        assert len(added) == len(
            tanks_remove
        ), f"incorrect number of added tanks reported {len(added) } != {len(tanks_remove)}"
        assert len(updated) == len(
            tanks_updated
        ), f"incorrect number of updated tanks reported {len(updated) } != {len(tanks_updated)}"


@pytest.mark.asyncio
@WGAPI_TANKSTR
async def test_7_api_tankstrs(
    datafiles: Path, wgapi_tankstrs_user_strings: list[str]
) -> None:
    """test for WGApiTankString()"""
    for fn in datafiles.iterdir():
        try:
            tank_str: WGApiTankString
            if (res := await WGApiTankString.open_json(fn)) is not None:
                tank_str = res
            else:
                raise ValueError(f"could read WGApiTankString from file: {fn}")
        except Exception as err:
            assert (
                False
            ), f"failed to parse test file as WGApiTankString(): {fn.name}: {err}"
        if (tank := Tank.transform(tank_str)) is None:
            assert (
                False
            ), f"could not transform WGApiTankString() to Tank(): {tank_str.user_string}"

    async with WGApi() as wg:
        for user_str in wgapi_tankstrs_user_strings:
            if (tank_str2 := await wg.get_tank_str(user_str)) is None:
                assert False, f"could not fetch WGApiTankString() for: {user_str}"
            assert (
                tank := Tank.transform(tank_str2)
            ) is not None, f"could not transform WGApiTankString({user_str}) to Tank()"
            assert (
                tank.name == tank_str2.user_string
            ), f"incorrect tank name: {user_str}"
            assert tank.tank_id == tank_str2.id, f"incorrect tank_id: {user_str}"
