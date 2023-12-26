import pytest  # type: ignore
from pathlib import Path
from random import choice
import logging
from blitzmodels import (  # noqa: E402
    WGApiWoTBlitzTankopedia,
    Maps,
)

from blitzmodels.wotinspector.wi_apiv1 import (  # noqa: E402
    ReplayJSON,
    ReplayFile,
    WoTinspector,
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

# 1) Parse test replay
# 2) Export test replays
# 3) Re-import test replays

########################################################
#
# Fixtures
#
########################################################

FIXTURE_DIR = Path(__file__).parent

REPLAY_JSON_FILES = pytest.mark.datafiles(
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
    on_duplicate="overwrite",
)

REPLAY_FILES = pytest.mark.datafiles(
    FIXTURE_DIR / "20200229_2321__jylpah_E-50_fort.wotbreplay",
    FIXTURE_DIR / "20200229_2324__jylpah_E-50_erlenberg.wotbreplay",
    FIXTURE_DIR / "20200229_2328__jylpah_E-50_grossberg.wotbreplay",
    FIXTURE_DIR / "20200229_2332__jylpah_E-50_lumber.wotbreplay",
    FIXTURE_DIR / "20200229_2337__jylpah_E-50_skit.wotbreplay",
    FIXTURE_DIR / "20200229_2341__jylpah_E-50_erlenberg.wotbreplay",
    FIXTURE_DIR / "20200229_2344__jylpah_E-50_rock.wotbreplay",
    FIXTURE_DIR / "20200229_2349__jylpah_E-50_himmelsdorf.wotbreplay",
    FIXTURE_DIR / "20200229_2353__jylpah_E-50_fort.wotbreplay",
    FIXTURE_DIR / "20200301_0022__jylpah_E-50_rudniki.wotbreplay",
    FIXTURE_DIR / "20200301_0026__jylpah_E-50_himmelsdorf.wotbreplay",
    FIXTURE_DIR / "20200301_0030__jylpah_E-50_rift.wotbreplay",
    FIXTURE_DIR / "20200301_0035__jylpah_E-50_rock.wotbreplay",
    FIXTURE_DIR / "20200301_0039__jylpah_E-50_desert_train.wotbreplay",
    on_duplicate="overwrite",
)


MAPS_JSON: str = "05_Maps_new.json"

MAPS = pytest.mark.datafiles(FIXTURE_DIR / MAPS_JSON, on_duplicate="overwrite")

TANKOPEDIA_JSON: str = "01_Tankopedia.json"
TANKOPEDIA = pytest.mark.datafiles(
    FIXTURE_DIR / TANKOPEDIA_JSON, on_duplicate="overwrite"
)


def get_player(fn: Path) -> str:
    parts: list[str] = fn.name.split("_")
    return parts[3]


def get_tank(fn: Path) -> str:
    parts: list[str] = fn.name.split("_")
    return parts[4]


def get_map(fn: Path) -> str:
    parts: list[str] = fn.name.split("_")
    return "_".join(parts[5:]).removesuffix(".wotbreplay")


# @pytest.fixture
# def get_tankopedia() -> WGApiWoTBlitzTankopedia:
#     with open(tmp_path / fn, "r") as f:
#         if (tp := WGApiWoTBlitzTankopedia.model_validate_json(f.read())) is not None:
#             return tp
#     raise ValueError(f"could not open tankopedia: {fn}")


# @pytest.fixture
# def get_maps(tmp_path: Path, fn: str = MAPS_JSON) -> Maps:
#     with open(tmp_path / fn, "r") as f:
#         if (tp := Maps.model_validate_json(f.read())) is not None:
#             return tp
#     raise ValueError(f"could not open maps: {fn}")


########################################################
#
# Tests
#
########################################################


@pytest.mark.asyncio
@REPLAY_JSON_FILES
async def test_1_import_export_replays(datafiles: Path, tmp_path: Path) -> None:
    for replay_file in datafiles.iterdir():
        debug("replay: %s", replay_file.name)
        replay = await ReplayJSON.open_json(replay_file)
        assert replay is not None, f"failed to import replay: {replay_file.name}"
        assert replay.is_ok, f"replay status is not OK: {replay_file.name}"

        debug(
            "%s: testing get_players(), get_allies(), get_enemies()",
            replay_file.name,
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
            debug("%s: testing platoon extraction", replay_file.name)
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
        ), f"failed to re-import replay: {replay_file.name}"
        assert (
            imported_replay.is_ok
        ), f"reimported replay status is not OK: {replay_file.name}"

        # compare original and re-imported replay
        # replay.store_id()
        # imported_replay.store_id()
        assert (
            replay.id == imported_replay.index
        ), "re-imported replay's id does not match"
        assert (
            replay.data.summary.title == imported_replay.data.summary.title
        ), "re-imported replays data.summary.title does not match"
        assert (
            replay.data.summary.vehicle == imported_replay.data.summary.vehicle
        ), "re-imported replays data.summary.vehicle does not match"
        assert (
            replay.data.summary.arena_unique_id
            == imported_replay.data.summary.arena_unique_id
        ), "re-imported replays data.summary.arena_unique_id does not match"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "file,md5hash",
    [
        (
            "20200229_2321__jylpah_E-50_fort.wotbreplay",
            "63dcc17340d3ce23e5b036a895d3d205",
        ),
        (
            "20200229_2324__jylpah_E-50_erlenberg.wotbreplay",
            "6232c7aa4cb419b73f295cff77231019",
        ),
        (
            "20200229_2328__jylpah_E-50_grossberg.wotbreplay",
            "4b2698b168edea033c0fbb87feef2b8b",
        ),
        (
            "20200229_2332__jylpah_E-50_lumber.wotbreplay",
            "87a4b4f822bc0d8b72680e21ea8621f4",
        ),
        (
            "20200229_2337__jylpah_E-50_skit.wotbreplay",
            "15306c49b1a74e52fa5d0ccc31940af3",
        ),
        (
            "20200229_2341__jylpah_E-50_erlenberg.wotbreplay",
            "7a660ed698c72d38482ae63af5303c0f",
        ),
        (
            "20200229_2344__jylpah_E-50_rock.wotbreplay",
            "52f09faf6b6d871bdbbd8181fc1c009f",
        ),
        (
            "20200229_2349__jylpah_E-50_himmelsdorf.wotbreplay",
            "cdb1cc750f365020f5854f4ab14968da",
        ),
        (
            "20200229_2353__jylpah_E-50_fort.wotbreplay",
            "cffd30be46d6a6361a3c22a2f6fdc064",
        ),
        (
            "20200301_0022__jylpah_E-50_rudniki.wotbreplay",
            "1efaabe632bc8ccf6ef563269da107f1",
        ),
        (
            "20200301_0026__jylpah_E-50_himmelsdorf.wotbreplay",
            "13c13175eef4ad838533805e4884047e",
        ),
        (
            "20200301_0030__jylpah_E-50_rift.wotbreplay",
            "38d8bca4b90eac91b1bc41dd7b0a401e",
        ),
        (
            "20200301_0035__jylpah_E-50_rock.wotbreplay",
            "762602554b903eef4800023b1e2df1c5",
        ),
        (
            "20200301_0039__jylpah_E-50_desert_train.wotbreplay",
            "60c14b403d7aafb1d3fd56a90a3b2592",
        ),
    ],
)
@MAPS
@TANKOPEDIA
@REPLAY_FILES
async def test_2_read_replay_meta(
    datafiles: Path,
    tmp_path: Path,
    file: str,
    md5hash: str,
) -> None:
    replay_fn = tmp_path / file
    debug("replay: %s", file)
    replay = ReplayFile(replay_fn)
    await replay.open()

    assert replay.is_opened, f"failed to open replay file: {replay_fn.name}"
    assert replay.meta.playerName == get_player(
        replay_fn
    ), f"incorrect player name: {replay.meta.playerName} != {get_player(replay_fn)}"

    assert replay.meta.mapName == get_map(
        replay_fn
    ), f"incorrect map name: {replay.meta.mapName} != {get_map(replay_fn)}"

    assert replay.meta.playerVehicleName == get_tank(
        replay_fn
    ), f"incorrect tank name: {replay.meta.playerVehicleName} != {get_tank(replay_fn)}"

    assert (
        replay.hash == md5hash
    ), f"MD5 has does not math: hash={replay.hash}, MD5={md5hash}"


@pytest.mark.asyncio
@TANKOPEDIA
@MAPS
@REPLAY_FILES
async def test_3_read_replays(
    datafiles: Path,
    tmp_path: Path,
    tankopedia_fn: Path = Path(TANKOPEDIA_JSON),
    maps_fn: Path = Path(MAPS_JSON),
) -> None:
    tankopedia: WGApiWoTBlitzTankopedia | None
    maps: Maps | None
    if (
        tankopedia := await WGApiWoTBlitzTankopedia.open_json(tmp_path / tankopedia_fn)
    ) is None:
        assert False, f"could not open tankopedia {tankopedia_fn}"
    if (maps := await Maps.open_json(tmp_path / maps_fn)) is None:
        assert False, f"could not open maps {maps_fn}"

    for replay_fn in datafiles.iterdir():
        if replay_fn.suffix != ".wotbreplay":
            continue
        debug("replay: %s", replay_fn.name)
        replay = ReplayFile(replay_fn)
        await replay.open()

        assert replay.is_opened, f"failed to open replay file: {replay_fn.name}"
        assert (
            len(replay.meta.update_title(tankopedia=tankopedia, maps=maps)) > 0
        ), f"could not update title with tankopedia & maps: {replay_fn.name}"


@pytest.mark.asyncio
@TANKOPEDIA
@MAPS
@REPLAY_FILES
async def test_4_post_replay(
    datafiles: Path,
    tmp_path: Path,
    tankopedia_fn: Path = Path(TANKOPEDIA_JSON),
    maps_fn: Path = Path(MAPS_JSON),
) -> None:
    tankopedia: WGApiWoTBlitzTankopedia | None
    maps: Maps | None
    uploaded_by: int = 521458531  # jylpah@EU
    max_replays: int = 2
    if (
        tankopedia := await WGApiWoTBlitzTankopedia.open_json(tmp_path / tankopedia_fn)
    ) is None:
        assert False, f"could not open tankopedia {tankopedia_fn}"
    if (maps := await Maps.open_json(tmp_path / maps_fn)) is None:
        assert False, f"could not open maps {maps_fn}"

    WI = WoTinspector()
    try:
        for replay_fn in datafiles.iterdir():
            if replay_fn.suffix != ".wotbreplay":
                continue
            fetch_json: bool = max_replays % 2 == 0
            debug("replay: %s", replay_fn.name)
            replay_id, replay_json = await WI.post_replay(
                replay_fn,
                uploaded_by=uploaded_by,
                tankopedia=tankopedia,
                maps=maps,
                fetch_json=fetch_json,
            )
            assert replay_id is not None, f"could not post a replay: {replay_fn.name}"
            assert not fetch_json or isinstance(
                replay_json, ReplayJSON
            ), f"did not receive ReplayJSON: type={type(replay_json)}, replay_json={replay_json}"
            if (max_replays := max_replays - 1) <= 0:
                break
    finally:
        await WI.close()


def test_5_replay_example_instance() -> None:
    try:
        _ = ReplayJSON.example_instance()
    except Exception as err:
        assert (
            False
        ), f"Could not validate ReplayJSON example instance : {type(err)}: {err}"
