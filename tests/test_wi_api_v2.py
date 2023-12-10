import sys
import pytest  # type: ignore
import pytest_asyncio
from os.path import dirname, realpath, join as pjoin, basename
from pathlib import Path
import logging
from typing import Dict, List, Any
from configparser import ConfigParser
import json

logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug

sys.path.insert(0, str(Path(__file__).parent.parent.resolve() / "src"))

from blitzutils.wotinspector.wi_apiv2 import (
    Replay,
    PlayerData,
    ReplaySummary,
    WotInspector,
)

from blitzutils import get_config_file

########################################################
#
# Test Plan
#
########################################################

# 1) test models
# 2) Test iterate over  replay list
# 3) test get a Replay

########################################################
#
# Fixtures
#
########################################################

FIXTURE_DIR = Path(__file__).parent


@pytest.fixture
def replay_ids_ok() -> List[str]:
    return ["22a56c4be013915002b82403fa8cf375"]


@pytest.fixture
def replay_list_filters() -> Dict[str, Any]:
    return {
        "player": 521458531,  # jylpah@EU
        "tier": 10,
    }


@pytest_asyncio.fixture(scope="function")
async def wotinspector() -> WotInspector:
    WI_AUTH_TOKEN: str | None = None
    WI_RATE_LIMIT: float = 20 / 3600
    config_file: Path | None = get_config_file()
    config = ConfigParser()
    if config_file is not None:
        config.read(config_file)
    WI_AUTH_TOKEN = config.get("WOTINSPECTOR", "auth_token", fallback=WI_AUTH_TOKEN)
    WI_RATE_LIMIT = config.getfloat(
        "WOTINSPECTOR", "rate_limit", fallback=WI_RATE_LIMIT
    )
    return WotInspector(auth_token=WI_AUTH_TOKEN, rate_limit=WI_RATE_LIMIT)


########################################################
#
# Tests
#
########################################################


@pytest.mark.asyncio
async def test_1_models() -> None:
    """test for models"""
    assert (
        r := Replay.example_instance()
    ) is not None, "could not parse the Replay example instance"
    assert (
        pd := PlayerData.example_instance()
    ) is not None, "could not parse the PlayerData example instance"


@pytest.mark.asyncio
async def test_2_get_replay_list(
    wotinspector: WotInspector, replay_list_filters: Dict[str, Any]
) -> None:
    """test /v2/blitz/replays/"""
    rl: ReplaySummary

    async for rl in wotinspector.list_replays(max_pages=2, **replay_list_filters):
        assert isinstance(
            rl, ReplaySummary
        ), f"WotInspector.list_replays() did not return 'ReplaySummary', but {type(rl)}"
        assert (
            isinstance(rl.id, str) and len(rl.id) > 5
        ), f"replay summary does not have proper id: {rl.id}"
    await wotinspector.close()


@pytest.mark.asyncio
async def test_3_get_replay(
    wotinspector: WotInspector, replay_ids_ok: List[str]
) -> None:
    """test /v2/blitz/replays/{id}"""
    r: Replay | None
    for replay_id in replay_ids_ok:
        assert (
            r := await wotinspector.get_replay(replay_id)
        ) is not None, f"could not retrieve replay_id={replay_id}"
        assert isinstance(r, Replay), f"replay_id={replay_id} is not type of 'Replay'"
    await wotinspector.close()
