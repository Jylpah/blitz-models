import sys
import pytest  # type: ignore
from os.path import dirname, realpath, join as pjoin, basename
from pathlib import Path
from typing import Tuple
import logging

logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug

sys.path.insert(0, str(Path(__file__).parent.parent.resolve() / "src"))

from blitzutils import Map, Maps, MapMode


########################################################
#
# Test Plan
#
########################################################

# 1) Read legacy JSON format
# 2) Write new format
# 3) Read new format

########################################################
#
# Fixtures
#
########################################################

FIXTURE_DIR = Path(dirname(realpath(__file__)))

MAPS_JSON: str = "05_Maps.json"
MAPS_OLD_JSON: str = "05_Maps_old.json"

MAPS = pytest.mark.datafiles(
    FIXTURE_DIR / "05_Maps.json",
    FIXTURE_DIR / "05_Maps_old.json",
)


@pytest.fixture
def maps_all() -> int:
    return 58  # number of maps 05_Maps.json


@pytest.fixture
def maps_added_updated() -> Tuple[int, int]:
    return (3, 1)  # number changes: 05_Maps_old.json vs maps 05_Maps.json


########################################################
#
# Tests
#
########################################################


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "file,count",
    [
        (MAPS_JSON, 58),
        (MAPS_OLD_JSON, 55),
    ],
)
@MAPS
async def test_1_import_export(
    tmp_path: Path, datafiles: Path, file: str, count: int
) -> None:
    maps: Maps | None
    maps_fn: Path = tmp_path / file
    assert (
        maps := await Maps.open_json(str(maps_fn.resolve()))
    ) is not None, f"could not parse Maps from {maps_fn.name}"

    assert (
        len(maps) == count
    ), f"could not import all maps: got {len(maps)}, expected {count}"

    maps_export_fn: str = f"{tmp_path.resolve()}/maps-export.json"
    await maps.save_json(maps_export_fn)

    maps_new: Maps | None = await Maps.open_json(maps_export_fn)
    assert maps_new is not None, "could not import exported Maps from JSON"

    assert (
        len(maps_new) == count
    ), f"could not import all maps: got {len(maps_new)}, expected {count}"


@pytest.mark.asyncio
@MAPS
async def test_2_update(
    tmp_path: Path, datafiles: Path, maps_added_updated: tuple[int, int]
) -> None:
    maps: Maps | None

    maps_old_fn: Path = tmp_path / MAPS_OLD_JSON
    assert (
        maps_old := await Maps.open_json(str(maps_old_fn.resolve()))
    ) is not None, f"could not parse Maps from {maps_old_fn.name}"

    maps_new_fn: Path = tmp_path / MAPS_JSON
    assert (
        maps_new := await Maps.open_json(str(maps_new_fn.resolve()))
    ) is not None, f"could not parse Maps from {maps_new_fn.name}"

    (added, updated) = maps_old.update(maps_new)

    assert maps_added_updated[0] == len(
        added
    ), f"could not import all maps: got {len(added)}, expected {maps_added_updated[0]}"

    assert maps_added_updated[1] == len(
        updated
    ), f"could not import all maps: got {len(updated)}, expected {maps_added_updated[0]}"
