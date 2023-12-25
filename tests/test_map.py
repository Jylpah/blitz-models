import sys
import pytest  # type: ignore
from pathlib import Path
from typing import Tuple
import logging

logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug

sys.path.insert(0, str(Path(__file__).parent.parent.resolve() / "src"))

from blitzmodels import Maps, MapMode, MapModeStr  # noqa: E402


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

FIXTURE_DIR = Path(__file__).parent

MAPS_JSON: str = "05_Maps.json"
MAPS_OLD_JSON: str = "05_Maps_old.json"
MAPS_NEW_JSON: str = "05_Maps_new.json"

MAPS = pytest.mark.datafiles(
    FIXTURE_DIR / MAPS_JSON,
    FIXTURE_DIR / MAPS_OLD_JSON,
    FIXTURE_DIR / MAPS_NEW_JSON,
    on_duplicate="overwrite",
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
    [(MAPS_JSON, 58), (MAPS_OLD_JSON, 55), (MAPS_NEW_JSON, 58)],
)
@MAPS
async def test_1_import_export(
    datafiles: Path, tmp_path: Path, file: str, count: int
) -> None:
    maps: Maps | None
    maps_fn: Path = tmp_path / file
    assert maps_fn.is_file(), f"could not find maps file: {maps_fn}"
    assert (
        maps := await Maps.open_json(maps_fn)
    ) is not None, f"could not open maps from: {maps_fn}"

    assert (
        len(maps) == count
    ), f"could not import all maps: got {len(maps)}, expected {count}"

    maps_export_fn: Path = tmp_path / "maps-export.json"
    assert (
        await maps.save_json(maps_export_fn) > 0
    ), f"could not write maps to file: {maps_export_fn}"

    assert (
        maps := await Maps.open_json(maps_export_fn)
    ) is not None, f"could not open maps from: {maps_export_fn}"

    assert (
        len(maps) == count
    ), f"could not import all maps: got {len(maps)}, expected {count}"


@pytest.mark.asyncio
@MAPS
async def test_2_update(
    tmp_path: Path, datafiles: Path, maps_added_updated: tuple[int, int]
) -> None:
    maps_old: Maps | None
    maps_new: Maps | None

    maps_old_fn: Path = tmp_path / MAPS_OLD_JSON

    assert (
        maps_old := await Maps.open_json(maps_old_fn)
    ) is not None, f"could not open maps from: {maps_old_fn.name}"

    maps_new_fn: Path = tmp_path / MAPS_JSON
    assert (
        maps_new := await Maps.open_json(maps_new_fn)
    ) is not None, f"could not open maps from: {maps_new_fn.name}"

    (added, updated) = maps_old.update(maps_new)

    assert maps_added_updated[0] == len(
        added
    ), f"could not import all maps: got {len(added)}, expected {maps_added_updated[0]}"

    assert maps_added_updated[1] == len(
        updated
    ), f"could not import all maps: got {len(updated)}, expected {maps_added_updated[0]}"


@pytest.mark.asyncio
@pytest.mark.datafiles(FIXTURE_DIR / MAPS_JSON, on_duplicate="overwrite")
async def test_3_mapmode(tmp_path: Path, datafiles: Path) -> None:
    maps_fn: Path = Path("__not_existing__")
    maps: Maps | None = None
    for fn in datafiles.iterdir():
        maps_fn = fn

    assert (
        maps := await Maps.open_json(maps_fn)
    ) is not None, f"could not open maps from: {maps_fn.name}"

    map_mode: MapMode
    map_mode_str: MapModeStr
    for map in maps:
        map_mode = map.mode
        map_mode_str = map_mode.toMapModeStr
        assert map_mode.name == map_mode_str.name, "conversion to MapModeStr"
        assert map_mode == map_mode_str.toMapMode, "conversion back to MapMode failed"
