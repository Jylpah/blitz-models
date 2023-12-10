import sys
import pytest  # type: ignore
from os.path import dirname, realpath, join as pjoin, basename
from pathlib import Path
import logging
import json

logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug

sys.path.insert(0, str(Path(__file__).parent.parent.resolve() / "src"))


from blitzutils.wotinspector.wi_apiv2 import Replay, PlayerData

########################################################
#
# Test Plan
#
########################################################

# 1) test models

########################################################
#
# Fixtures
#
########################################################

FIXTURE_DIR = Path(__file__).parent


@pytest.mark.asyncio
async def test_1_models() -> None:
    """test for models"""
    assert (
        r := Replay.example_instance()
    ) is not None, "could not parse the Replay example instance"
    assert (
        pd := PlayerData.example_instance()
    ) is not None, "could not parse the PlayerData example instance"
