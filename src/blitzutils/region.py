"""
class Region(StrEnum) to denote (server) region in WoT Blitz

"""

from enum import StrEnum

MAX_UINT32: int = 4294967295


class Region(StrEnum):
    ru = "ru"
    eu = "eu"
    com = "com"
    asia = "asia"
    china = "china"
    bot = "BOTS"

    @classmethod
    def API_regions(cls) -> set["Region"]:
        # RU removed 2023-04-28 since the app-id does not work anymore
        return {Region.eu, Region.com, Region.asia}

    @classmethod
    def has_stats(cls) -> set["Region"]:
        # RU removed 2023-04-28 since the app-id does not work anymore
        return {Region.eu, Region.com, Region.asia}

    @property
    def id_range(self) -> range:
        if self == Region.ru:
            return range(0, int(5e8))
        elif self == Region.eu:
            return range(int(5e8), int(10e8))
        elif self == Region.com:
            return range(int(10e8), int(20e8))
        elif self == Region.asia:
            return range(int(20e8), int(31e8))
        elif self == Region.china:
            return range(int(31e8), int(42e8))
        elif self == Region.bot:
            return range(int(42e8), MAX_UINT32 + 1)
        else:
            raise ValueError(f"Unknown region: {self}")

    @property
    def id_range_players(self) -> range:
        """Method needed for account_id farming fro WG ID
        For some reasons Asia server has few account_ids
        between  30e8 - 31e8. These could be press accounts.
        These accounts do not have stats in the API
        """
        if self == Region.ru:
            return range(0, int(5e8))
        elif self == Region.eu:
            return range(int(5e8), int(10e8))
        elif self == Region.com:
            return range(int(10e8), int(20e8))
        elif self == Region.asia:
            # note the range
            return range(int(20e8), int(30e8))
        elif self == Region.china:
            return range(int(31e8), int(42e8))
        else:
            return range(int(42e8), MAX_UINT32 + 1)

    @classmethod
    def from_id(cls, account_id: int) -> "Region":
        try:
            if account_id >= 42e8:
                return Region.bot  # bots, same IDs on every server
            elif account_id >= 31e8:
                return Region.china
            elif account_id >= 20e8:
                return Region.asia
            elif account_id >= 10e8:
                return Region.com
            elif account_id >= 5e8:
                return Region.eu
            elif account_id >= 0:
                return Region.ru
            else:
                raise ValueError(f"account_id is out of id_range: {account_id}")
        except Exception as err:
            raise ValueError(f"accunt_id {account_id} is out of known id range: {err}")

    def matches(self, other_region: "Region") -> bool:
        assert type(other_region) is type(self), "other_region is not Region"
        return self == other_region
