import sys
import pytest  # type: ignore
from os.path import basename
from pathlib import Path
import logging

from pyutils import awrap
from pydantic_exportables import export

sys.path.insert(0, str(Path(__file__).parent.parent.resolve() / "src"))

from blitzmodels import Account

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

# 1) Parse account list for CSV
# 2) Export accounts to JSON
# 3) re-import from JSON and compare


########################################################
#
# Fixtures
#
########################################################

FIXTURE_DIR = Path(__file__).parent

ACCOUNTS_CSV = pytest.mark.datafiles(
    FIXTURE_DIR / "03_Accounts.csv",
    on_duplicate="overwrite",
)
ACCOUNTS_TXT = pytest.mark.datafiles(
    FIXTURE_DIR / "03_Accounts1.txt",
    FIXTURE_DIR / "03_Accounts2.txt",
    on_duplicate="overwrite",
)


@pytest.fixture
def accounts_count() -> int:
    return 500  # accounts in the CSV and TXT files


########################################################
#
# Tests
#
########################################################


@pytest.mark.asyncio
@ACCOUNTS_CSV
async def test_1_import_export_accounts(
    datafiles: Path, tmp_path: Path, accounts_count: int
) -> None:
    for accounts_file in datafiles.iterdir():
        accounts: list[Account] = list()

        accounts_filename: str = str(accounts_file.resolve())
        debug("replay: %s", basename(accounts_filename))
        async for account in Account.import_csv(accounts_filename):
            debug("imported Account() from CSV: %s", str(account))
            accounts.append(account)

        assert (
            len(accounts) == accounts_count
        ), f"could not import all the accounts: {len(accounts)} != {accounts_count}"

        # export loaded replay as JSON
        json_filename: str = str(tmp_path / "export_accounts.json")
        await export(awrap(accounts), "json", json_filename)

        imported_accounts: list[Account] = list()
        async for account in Account.import_file(json_filename):
            imported_accounts.append(account)

        assert (
            len(imported_accounts) == accounts_count
        ), f"could not import all the accounts from JSON: {len(imported_accounts)} != {accounts_count}"

        for ndx, account in enumerate(accounts):
            assert (
                imported_accounts[ndx] == account
            ), f"imported accounts in wrong order: {imported_accounts[ndx]} != {account}"

        # export loaded replay as CSV
        csv_filename: str = str(tmp_path / "export_accounts.csv")
        await export(awrap(accounts), "csv", csv_filename)

        imported_accounts = list()
        async for account in Account.import_file(csv_filename):
            imported_accounts.append(account)

        assert (
            len(imported_accounts) == accounts_count
        ), f"could not import all the accounts from JSON: {len(imported_accounts)} != {accounts_count}"

        for ndx, account in enumerate(accounts):
            assert (
                imported_accounts[ndx] == account
            ), f"imported accounts in wrong order: {imported_accounts[ndx]} != {account}"

        assert (
            len(set(imported_accounts)) == accounts_count
        ), "some accounts imported as duplicate"


@pytest.mark.asyncio
@ACCOUNTS_TXT
async def test_2_import_export_accounts_txt(
    datafiles: Path, tmp_path: Path, accounts_count: int
) -> None:
    for accounts_file in datafiles.iterdir():
        accounts: set[Account] = set()

        accounts_filename: str = str(accounts_file.resolve())
        debug("replay: %s", basename(accounts_filename))
        async for account in Account.import_txt(accounts_filename):
            debug("imported Account() from TXT: %s", str(account))
            accounts.add(account)

        assert (
            len(accounts) == accounts_count
        ), f"could not import all the accounts: {len(accounts)} != {accounts_count}"
