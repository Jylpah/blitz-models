import sys
import pytest  # type: ignore
from os.path import dirname, realpath, join as pjoin, basename
from pathlib import Path
from random import choice
import logging

logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug

sys.path.insert(0, str(Path(__file__).parent.parent.resolve() / "src"))

from blitzutils import (
    ReplayJSON,
)


########################################################
#
# Test Plan
#
########################################################

# 1) Parse test replay
# 2) Export test replays
# 3) Re-import test replays

########################################################
#
# Fixtures
#
########################################################

FIXTURE_DIR = Path(dirname(realpath(__file__)))

REPLAY_FILES = pytest.mark.datafiles(
    FIXTURE_DIR / "20200229_2321__jylpah_E-50_fort.wotbreplay.json",
    FIXTURE_DIR / "20200229_2324__jylpah_E-50_erlenberg.wotbreplay.json",
    FIXTURE_DIR / "20200229_2328__jylpah_E-50_grossberg.wotbreplay.json",
    FIXTURE_DIR / "20200229_2332__jylpah_E-50_lumber.wotbreplay.json",
    FIXTURE_DIR / "20200229_2337__jylpah_E-50_skit.wotbreplay.json",
    FIXTURE_DIR / "20200229_2341__jylpah_E-50_erlenberg.wotbreplay.json",
    FIXTURE_DIR / "20200229_2344__jylpah_E-50_rock.wotbreplay.json",
    FIXTURE_DIR / "20200229_2349__jylpah_E-50_himmelsdorf.wotbreplay.json",
    FIXTURE_DIR / "20200229_2353__jylpah_E-50_fort.wotbreplay.json",
    FIXTURE_DIR / "20200301_0022__jylpah_E-50_rudniki.wotbreplay.json",
    FIXTURE_DIR / "20200301_0026__jylpah_E-50_himmelsdorf.wotbreplay.json",
    FIXTURE_DIR / "20200301_0030__jylpah_E-50_rift.wotbreplay.json",
    FIXTURE_DIR / "20200301_0035__jylpah_E-50_rock.wotbreplay.json",
    FIXTURE_DIR / "20200301_0039__jylpah_E-50_desert_train.wotbreplay.json",
)


########################################################
#
# Tests
#
########################################################


@pytest.mark.asyncio
@REPLAY_FILES
async def test_1_import_export_replays(datafiles: Path, tmp_path: Path) -> None:
    for replay_file in datafiles.iterdir():
        replay_filename: str = str(replay_file.resolve())
        debug("replay: %s", basename(replay_filename))
        replay = await ReplayJSON.open_json(replay_filename)
        assert (
            replay is not None
        ), f"failed to import replay: {basename(replay_filename)}"
        assert replay.is_ok, f"replay status is not OK: {basename(replay_filename)}"

        debug(
            "%s: testing get_players(), get_allies(), get_enemies()",
            basename(replay_filename),
        )
        for _ in range(5):
            player: int = choice(replay.get_players())
            enemy: int = choice(replay.get_enemies(player))
            assert player in replay.get_enemies(
                enemy
            ), f"error in getting allies & enemies player={player}: enemy={enemy}"

        allied_platoons, enemy_platoons = replay.get_platoons()
        # this "should" always match in public games
        assert len(allied_platoons) == len(
            enemy_platoons
        ), f"number of platoons does not match: allied={len(allied_platoons)}, enemy={len(enemy_platoons)}"

        if len(allied_platoons) > 0:
            debug("%s: testing platoon extraction", basename(replay_filename))
            player = allied_platoons[1][0]
            enemy = enemy_platoons[1][1]
            assert enemy in replay.get_enemies(player), "platoon analysis failed"
        # export loaded replay
        export_filename: str = str(tmp_path / "export_replay.json")
        await replay.save_json(export_filename)

        # re-import exported replay
        imported_replay: ReplayJSON | None
        imported_replay = await ReplayJSON.open_json(export_filename)
        assert (
            imported_replay is not None
        ), f"failed to re-import replay: {basename(replay_filename)}"
        assert (
            imported_replay.is_ok
        ), f"reimported replay status is not OK: {basename(replay_filename)}"

        # compare original and re-imported replay
        # replay.store_id()
        # imported_replay.store_id()
        assert (
            replay.id == imported_replay.index
        ), f"re-imported replay's id does not match"
        assert (
            replay.data.summary.title == imported_replay.data.summary.title
        ), f"re-imported replays data.summary.title does not match"
        assert (
            replay.data.summary.vehicle == imported_replay.data.summary.vehicle
        ), f"re-imported replays data.summary.vehicle does not match"
        assert (
            replay.data.summary.arena_unique_id
            == imported_replay.data.summary.arena_unique_id
        ), f"re-imported replays data.summary.arena_unique_id does not match"
