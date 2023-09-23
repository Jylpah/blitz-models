import sys
import pytest  # type: ignore
from os.path import dirname, realpath, basename
from pathlib import Path
import logging

logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug

sys.path.insert(0, str(Path(__file__).parent.parent.resolve() / "src"))

from pyutils import export, awrap
from blitzutils import WoTBlitzRelease


########################################################
#
# Test Plan
#
########################################################

# 1) Parse release list for CSV
# 2) Export releases to JSON
# 3) re-import from JSON and compare


########################################################
#
# Fixtures
#
########################################################

FIXTURE_DIR = Path(dirname(realpath(__file__)))

REPLAY_FILES = pytest.mark.datafiles(FIXTURE_DIR / "02_Releases.csv")


@pytest.fixture
def releases_count() -> int:
    return 100  # releases in the CSV file


########################################################
#
# Tests
#
########################################################


@pytest.mark.asyncio
@REPLAY_FILES
async def test_1_import_export_releases(
    datafiles: Path, tmp_path: Path, releases_count: int
) -> None:
    for releases_file in datafiles.iterdir():
        releases: list[WoTBlitzRelease] = list()

        releases_filename: str = str(releases_file.resolve())
        debug("replay: %s", basename(releases_filename))
        async for release in WoTBlitzRelease.import_csv(releases_filename):
            releases.append(release)

        assert (
            len(releases) == releases_count
        ), f"could not import all the releases: {len(releases)} != {releases_count}"

        # export loaded replay as JSON
        json_filename: str = str(tmp_path / "export_release.json")
        await export(awrap(releases), "json", json_filename)

        imported_releases: list[WoTBlitzRelease] = list()
        async for release in WoTBlitzRelease.import_file(json_filename):
            imported_releases.append(release)

        assert (
            len(imported_releases) == releases_count
        ), f"could not import all the releases from JSON: {len(imported_releases)} != {releases_count}"

        for ndx, release in enumerate(releases):
            assert (
                imported_releases[ndx] == release
            ), f"imported releases in wrong order: {imported_releases[ndx]} != {release}"

        # export loaded replay as CSV
        csv_filename: str = str(tmp_path / "export_release.csv")
        await export(awrap(releases), "csv", csv_filename)

        imported_releases = list()
        async for release in WoTBlitzRelease.import_file(csv_filename):
            imported_releases.append(release)

        assert (
            len(imported_releases) == releases_count
        ), f"could not import all the releases from JSON: {len(imported_releases)} != {releases_count}"

        for ndx, release in enumerate(releases):
            assert (
                imported_releases[ndx] == release
            ), f"imported releases in wrong order: {imported_releases[ndx]} != {release}"

        assert (
            len(set(imported_releases)) == releases_count
        ), "some releases imported as duplicate"
