import sys
import pytest  # type: ignore
from os.path import dirname, realpath, join as pjoin, basename
from pathlib import Path
import aiofiles
from pydantic import BaseModel
import logging

logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug

sys.path.insert(0, str(Path(__file__).parent.parent.resolve() / "src"))

from blitzutils import WGTank, EnumNation, EnumVehicleTier, EnumVehicleTypeInt, EnumVehicleTypeStr
from blitzutils import WGApiTankopedia


########################################################
#
# Test Plan
#
########################################################

# EnumVehicleTypeInt/Str
# 1) Test creation
# 2) Test conversions
# 3) Test equality (pass/fail)
# 3) Test errors

########################################################
#
# Fixtures
#
########################################################


@pytest.fixture
def enum_vehicle_type_names() -> list[str]:
    return ["light_tank", "medium_tank", "heavy_tank", "tank_destroyer"]


@pytest.fixture
def enum_vehicle_type_str_values() -> list[str]:
    return ["lightTank", "mediumTank", "heavyTank", "AT-SPG"]


@pytest.fixture
def enum_vehicle_tier() -> list[str]:
    return ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]


@pytest.fixture
def enum_nation() -> list[str]:
    return ["ussr", "germany", "usa", "china", "france", "uk", "japan", "other", "european"]


@pytest.fixture
def tankopedia_tanks() -> int:
    return 592  # number of tanks in the 01_WGTanks.json


FIXTURE_DIR = Path(dirname(realpath(__file__)))
TANKS_JSON_FILES = pytest.mark.datafiles(FIXTURE_DIR / "01_WGTanks.json")


class TanksJsonList(BaseModel):
    __root__: list[WGTank] = list()

    def __iter__(self):
        return iter(self.__root__)

    def __getitem__(self, item):
        return self.__root__[item]

    def __len__(self) -> int:
        return len(self.__root__)


########################################################
#
# Tests
#
########################################################


def test_1_EnumVehicleTypeInt_create(enum_vehicle_type_names: list[str]) -> None:
    for ndx in range(len(enum_vehicle_type_names)):
        tank_type: str = enum_vehicle_type_names[ndx]
        try:
            assert (
                EnumVehicleTypeInt(ndx) is EnumVehicleTypeInt[tank_type]
            ), f"Creation of EnumVehicleTypeInt.{tank_type} failed"
        except Exception as err:
            assert False, f"Could not create EnumVehicleTypeInt of {tank_type}"


def test_2_EnumVehicleTypeInt_complete(enum_vehicle_type_names: list[str]) -> None:
    tank_types = set(EnumVehicleTypeInt)
    assert len(tank_types) == len(enum_vehicle_type_names), f"EnumVehicleTypeInt has wrong number of tank types"
    for tank_type in enum_vehicle_type_names:
        tank_types.remove(EnumVehicleTypeInt[tank_type])
    assert (
        len(tank_types) == 0
    ), f"EnumVehicleTypeInt does not have all the tank types: {' ,'.join([tti.name for tti in tank_types])}"


def test_3_EnumVehicleTypeStr_create(
    enum_vehicle_type_names: list[str], enum_vehicle_type_str_values: list[str]
) -> None:
    for ndx in range(len(enum_vehicle_type_names)):
        name: str = enum_vehicle_type_names[ndx]
        value: str = enum_vehicle_type_str_values[ndx]
        try:
            assert (
                EnumVehicleTypeStr(value) is EnumVehicleTypeStr[name]
            ), f"Creation of EnumVehicleTypeStr.{name} failed"
        except Exception as err:
            assert False, f"Could not create EnumVehicleTypeStr.{name}"


def test_4_EnumVehicleTypestr_complete(enum_vehicle_type_names: list[str]) -> None:
    tank_types = set(EnumVehicleTypeStr)
    assert len(tank_types) == len(enum_vehicle_type_names), f"EnumVehicleTypeStr has wrong number of tank types"
    for tank_type in enum_vehicle_type_names:
        tank_types.remove(EnumVehicleTypeStr[tank_type])
    assert (
        len(tank_types) == 0
    ), f"EnumVehicleTypeStr does not have all the tank types: {' ,'.join([tts.name for tts in tank_types])}"  # type: ignore


def test_5_EnumVehicleType_conversion() -> None:
    """Test converstions between EnumVehicleTypeInt and EnumVehicleTypeStr"""
    for tt_int in EnumVehicleTypeInt:
        tt_str: EnumVehicleTypeStr = tt_int.as_str
        assert (
            tt_int.name == tt_str.name
        ), f"Conversion from EnumVehicleTypeInt to EnumVehicleTypeStr failed: {tt_int.name}"
        assert EnumVehicleTypeInt.from_str(tt_str.value) is tt_int, f"from_str() failed for {tt_str}"
        assert (
            tt_int is tt_str.as_int
        ), f"Conversion from EnumVehicleTypeStr to EnumVehicleTypeInt failed: {tt_int.name}"
        assert EnumVehicleTypeStr.from_int(tt_int.value) is tt_str, f"from_int() failed for {tt_int}"


def test_6_EnumVehicleTier_create(enum_vehicle_tier) -> None:
    for ndx, tier_str in enumerate(enum_vehicle_tier):
        tier_int: int = ndx + 1

        assert (
            EnumVehicleTier(tier_int) is EnumVehicleTier[tier_str]
        ), f"Failed to create EnumVehicleTier for {tier_str}"
        assert EnumVehicleTier.read_tier(tier_str) is EnumVehicleTier[tier_str], f"read_tier({tier_str}) failed"
        assert EnumVehicleTier.read_tier(str(tier_int)) is EnumVehicleTier[tier_str], f"read_tier({tier_int}) failed"
        assert EnumVehicleTier(tier_int) == tier_int, f"EnumVehicleTier.N != N for {tier_int}"


def test_7_EnumNation_create(enum_nation: list[str]) -> None:
    for nation in enum_nation:
        assert EnumNation[nation].name == nation, f"Failed to create EnumNation for {nation}"


@pytest.mark.asyncio
@TANKS_JSON_FILES
async def test_8_Tank_import(datafiles: Path) -> None:
    tanks_json = TanksJsonList()
    for tanks_json_fn in datafiles.iterdir():
        async with aiofiles.open(tanks_json_fn) as file:
            try:
                tanks_json = TanksJsonList.parse_raw(await file.read())
            except Exception as err:
                assert False, f"Parsing test file List[Tank] failed: {basename(tanks_json_fn)}"
        tanks: set[int] = set([tank.tank_id for tank in tanks_json])
        assert len(tanks) == len(tanks_json), f"Parsing test file List[Tank] failed: {basename(tanks_json_fn)}"
        assert len(tanks_json) > 0, f"could not parse any Tank from file: {basename(tanks_json_fn)}"


@pytest.mark.asyncio
@TANKS_JSON_FILES
async def test_9_WGApiTankopedia(datafiles: Path, tmp_path: Path, tankopedia_tanks: int) -> None:
    tankopedia = WGApiTankopedia()
    tanks_json = TanksJsonList()
    debug("should have %d tanks", tankopedia_tanks)
    for tanks_json_fn in datafiles.iterdir():
        async with aiofiles.open(tanks_json_fn) as file:
            try:
                tanks_json = TanksJsonList.parse_raw(await file.read())
            except Exception as err:
                assert False, f"Parsing test file List[Tank] failed: {basename(tanks_json_fn)}"
    for tank in tanks_json:
        tankopedia.add(tank)
    debug("read %d tanks", len(tankopedia.data))
    assert tankopedia.meta is not None, f"Failed to update meta"
    assert tankopedia.meta["count"] == len(tanks_json), f"failed to update meta.count"
    assert len(tanks_json) == len(tankopedia.data), f"could not add all the tanks to tankopedia"
    assert (
        len(tankopedia.data) == tankopedia_tanks
    ), f"could not import all the tanks: got {tankopedia.data}, should be {tankopedia_tanks}"

    # test tankopedia export import
    tankopedia_file: str = f"{tmp_path.resolve()}/tankopedia.json"
    try:
        await tankopedia.save_json(tankopedia_file)
    except Exception as err:
        assert False, f"could not export WGAPiTankopedia: {err}"

    tankopedia_imported: WGApiTankopedia
    imported: bool = False
    async for tp_imported in WGApiTankopedia.import_json(tankopedia_file):
        tankopedia_imported = tp_imported
        imported = True
        debug("imported tankopedia has %d tanks", len(tankopedia_imported.data))
        assert len(tankopedia.data) == len(tankopedia_imported.data), f"could not import all the tanks"

    assert imported, "could not import anything"
