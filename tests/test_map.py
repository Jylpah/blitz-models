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
MAPS = pytest.mark.datafiles(
    FIXTURE_DIR / "05_Maps.json",
)


@pytest.fixture
def maps_all() -> int:
    return 58  # number of maps 05_Maps.json


########################################################
#
# Tests
#
########################################################


@pytest.mark.asyncio
@MAPS
async def test_1_import_export(tmp_path: Path, datafiles: Path, maps_all: int) -> None:
    for maps_fn in datafiles.iterdir():
        maps: Maps | None
        assert (
            maps := await Maps.open_json(str(maps_fn.resolve()))
        ) is not None, f"could not parse Maps from {maps_fn.name}"

        assert len(maps) == maps_all, f"could not import all maps: got {len(maps)}, expected {maps_all}"

        maps_export_fn: str = f"{tmp_path.resolve()}/maps-export.json"
        await maps.save_json(maps_export_fn)

        maps_new: Maps | None = await Maps.open_json(maps_export_fn)
        assert maps_new is not None, "could not import exported Maps from JSON"

        assert len(maps_new) == maps_all, f"could not import all maps: got {len(maps_new)}, expected {maps_all}"
