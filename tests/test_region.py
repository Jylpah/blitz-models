import sys
import pytest # type: ignore
from os.path import dirname, realpath, join as pjoin
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.resolve() / 'src'))

from blitzutils import Region


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
	return [ 1234, 3463456, 2342323 ]

@pytest.fixture
def ids_eu() -> list[int]:
	return [ int(5e8), int(5e8) + 1342323, int(5e8) + 342323 ]

@pytest.fixture
def ids_com() -> list[int]:
	return [ int(10e8), int(10e8) + 23452, int(10e8) + 7845235 ]

@pytest.fixture
def ids_asia() -> list[int]:
	return [ int(20e8), int(20e8) + 23452, int(20e8) + 7845235 ]

@pytest.fixture
def ids_ru_fail() -> list[int]:
	return [ -1234, int(5e8) + 1 ]

@pytest.fixture
def ids_eu_fail() -> list[int]:
	return [ - int(5e8), 10000 , int(10e8) ]

@pytest.fixture
def ids_com_fail() -> list[int]:
	return [ int(10e8) -1 , int(20e8), -1  ]

@pytest.fixture
def ids_asia_fail() -> list[int]:
	return [ int(20e8)-1 , int(31e8), -1  ]


def test_1_create() -> None:
	for i in range(0, int(42e8), int(1e8)):
		r = Region.from_id(i)
		assert i in r.id_range, f"account_id ({i}) is outside region's ({r} id range)"


def test_2_ru(ids_ru, ids_ru_fail) -> None:
	for i in ids_ru:
		r = Region.from_id(i)
		assert r == Region.ru
	for i in ids_ru_fail:
		try:
			r = Region.from_id(i)
			assert r != Region.ru
		except ValueError:
			pass # OK


def test_3_eu(ids_eu, ids_eu_fail) -> None:
	for i in ids_eu:
		r = Region.from_id(i)
		assert r == Region.eu
	for i in ids_eu_fail:
		try:
			r = Region.from_id(i)
			assert r != Region.eu
		except ValueError:
			pass # OK


def test_4_com(ids_com, ids_com_fail) -> None:
	for i in ids_com:
		r = Region.from_id(i)
		assert r == Region.com
	for i in ids_com_fail:
		try:
			r = Region.from_id(i)
			assert r != Region.com
		except ValueError:
			pass # OK


def test_2_asia(ids_asia, ids_asia_fail) -> None:
	for i in ids_asia:
		r = Region.from_id(i)
		assert r == Region.asia
	for i in ids_asia_fail:
		try:
			r = Region.from_id(i)
			assert r != Region.asia
		except ValueError:
			pass # OK