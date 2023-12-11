import sys
import pytest  # type: ignore
from os.path import dirname, realpath, join as pjoin
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent.resolve() / "src"))

from blitzmodels import Region


########################################################
#
# Test Plan
#
########################################################

# 1) Create instances per region
# 2) Test equality (pass/fail)
# 3) Test errors


@pytest.fixture
def ids_ru() -> list[int]:
    return [1234, 3463456, 2342323]


@pytest.fixture
def ids_eu() -> list[int]:
    return [int(5e8), int(5e8) + 1342323, int(5e8) + 342323]


@pytest.fixture
def ids_com() -> list[int]:
    return [int(10e8), int(10e8) + 23452, int(10e8) + 7845235]


@pytest.fixture
def ids_asia() -> list[int]:
    return [int(20e8), int(20e8) + 23452, int(20e8) + 7845235]


@pytest.fixture
def ids_bots() -> list[int]:
    return [int(42e8), int(42e8) + 23452, int(42e8) + 7840525]


@pytest.fixture
def ids_ru_fail() -> list[int]:
    return [-1234, int(5e8) + 1]


@pytest.fixture
def ids_eu_fail() -> list[int]:
    return [-int(5e8), 10000, int(10e8)]


@pytest.fixture
def ids_com_fail() -> list[int]:
    return [int(10e8) - 1, int(20e8), -1]


@pytest.fixture
def ids_asia_fail() -> list[int]:
    return [int(20e8) - 1, int(31e8), -1]


@pytest.fixture
def ids_bots_fail() -> list[int]:
    return [int(42e8) - 1, int(20e8), -1]


def test_1_create() -> None:
    for i in range(0, int(30e8), int(1e8)):
        r = Region.from_id(i)
        assert i in r.id_range, f"account_id ({i}) is outside region's ({r} id range)"


def _do_test_region(
    region: Region, ids_ok: List[int], ids_nok: List[int], api: bool = True
) -> None:
    """ "Util function to run region tests"""
    assert (
        region in Region.API_regions()
    ) == api, f"Region {region} {'is not' if api else 'is'} in API regions"
    for i in ids_ok:
        r = Region.from_id(i)
        assert r == region, f"Region.from_id({i}) is not {region}, even it should"
        assert (
            i in region.id_range
        ), f"Region.from_id({i}) is not in {region} id range, even it should"
    for i in ids_nok:
        try:
            r = Region.from_id(i)
            assert (
                r != region
            ), f"Region.from_id() {r} is {region} even it should not be"
            assert (
                i not in region.id_range
            ), f"account_id={i} is in {region} id range even it should not be"
        except ValueError:
            pass  # OK


def test_2_ru(ids_ru: List[int], ids_ru_fail: List[int]) -> None:
    _do_test_region(Region.ru, ids_ru, ids_ru_fail, api=False)


def test_3_eu(ids_eu, ids_eu_fail) -> None:
    _do_test_region(Region.eu, ids_eu, ids_eu_fail, api=True)


def test_4_com(ids_com, ids_com_fail) -> None:
    _do_test_region(Region.com, ids_com, ids_com_fail, api=True)


def test_5_asia(ids_asia, ids_asia_fail) -> None:
    _do_test_region(Region.asia, ids_asia, ids_asia_fail, api=True)


def test_6_bots(ids_bots, ids_bots_fail) -> None:
    _do_test_region(Region.bot, ids_bots, ids_bots_fail, api=False)
