from typing import Any, Optional, Self, Dict
import logging
from bson.int64 import Int64
from pydantic import (
    field_validator,
    model_validator,
    ConfigDict,
    Field,
)

from pydantic_exportables import (
    CSVExportable,
    TXTExportable,
    JSONExportable,
    TXTImportable,
    Importable,
    Idx,
)

from .region import Region
from .wg_api import AccountInfo

logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug


# B = TypeVar("B", bound="BaseModel")

###########################################
#
# Account()
#
###########################################

TypeAccountDict = dict[str, int | bool | Region | None]


# def lateinit_region() -> Region:
#     """Required for initializing a model w/o a 'region' field"""
#     raise RuntimeError("lateinit_region(): should never be called")


class Account(JSONExportable, CSVExportable, TXTExportable, TXTImportable, Importable):
    # fmt: off
    id              : int       = Field(alias="_id")
    # lateinit is a trick to fool mypy since region is set in root_validator
    region          : Region    = Field(default=Region.bot, alias="r")
    last_battle_time: int       = Field(default=0, alias="l")
    created_at      : int       = Field(default=0, alias="c")
    updated_at      : int       = Field(default=0, alias="u")
    nickname        : str | None= Field(default=None, alias="n")
    # fmt: on

    model_config = ConfigDict(
        populate_by_name=True, frozen=False, validate_assignment=True
    )

    @property
    def index(self) -> Idx:
        return self.id

    @property
    def indexes(self) -> dict[str, Idx]:
        """return backend indexes"""
        if self.region is None:
            return {"region": "_none_", "account_id": self.id}
        else:
            return {"region": self.region.name, "account_id": self.id}

    @field_validator("id")
    @classmethod
    def check_id(cls, v):
        assert v is not None, "id cannot be None"
        assert isinstance(v, int), "id has to be int"
        if isinstance(v, Int64):
            v = int(v)
        if v < 0:
            raise ValueError("account_id must be >= 0")
        return v

    @field_validator("last_battle_time")
    @classmethod
    def check_epoch_ge_zero(cls, v: int) -> int:
        if v >= 0:
            return v
        else:
            raise ValueError("time field must be >= 0")

    @model_validator(mode="after")
    def set_region(self) -> Self:
        if self.region == Region.bot:  # Region.Bot is used as "NULL"
            self._set_skip_validation("region", Region.from_id(self.id))
        return self

    @model_validator(mode="before")
    def read_account_id_str(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Read account_id from string of format account_id:region"""
        _id: Any | None = None
        if "id" in values:  # since pre=True, has to check both field name and alias
            _id = values.get("id")
        elif "_id" in values:
            _id = values.get("_id")
        else:
            raise ValueError("No id or _id defined")

        if isinstance(_id, str):
            region: Region
            acc_id: list[str] = _id.split(":")
            account_id: int = int(acc_id[0])
            if len(acc_id) == 2:
                region = Region(acc_id[1])
            else:
                region = Region.from_id(account_id)
            values["id"] = account_id
            values["region"] = region
        return values

    # TXTExportable()
    def txt_row(self, format: str = "id") -> str:
        """export data as single row of text"""
        if format == "id":
            return str(self.id)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    # TXTImportable()
    @classmethod
    def from_txt(cls, text: str, **kwargs) -> Self:
        """export data as single row of text"""
        try:
            return cls(id=text, **kwargs)
        except Exception as err:
            raise ValueError(f"Could not create Account() with id={text}: {err}")

    def __str__(self) -> str:
        fields: list[str] = [f for f in self.model_fields.keys() if f != "id"]
        return f'{type(self).__name__} id={self.id}: { ", ".join( [ f + "=" + str(getattr(self,f)) for f in fields ]  ) }'

    @classmethod
    def transform_WGAccountInfo(cls, in_obj: "AccountInfo") -> Optional["Account"]:
        """Transform AccountInfo object to Account"""
        try:
            return Account(
                id=in_obj.account_id,
                region=in_obj.region,
                last_battle_time=in_obj.last_battle_time,
                created_at=in_obj.created_at,
                updated_at=in_obj.updated_at,
                nickname=in_obj.nickname,
            )
        except Exception as err:
            error(f"{err}")
        return None

    def update_info(self, update: "AccountInfo") -> bool:
        """Update Account() from WGACcountInfo i.e. from WG API"""
        updated: bool = False
        try:
            if (
                update.last_battle_time > 0
                and self.last_battle_time != update.last_battle_time
            ):
                self.last_battle_time = update.last_battle_time
                updated = True
            if update.created_at > 0 and update.created_at != self.created_at:
                self.created_at = update.created_at
                updated = True
            if update.updated_at > 0 and update.updated_at != self.updated_at:
                self.updated_at = update.updated_at
                updated = True
            if update.nickname is not None and (
                self.nickname is None or self.nickname != update.nickname
            ):
                self.nickname = update.nickname
                updated = True
        except Exception as err:
            error(f"{err}")
        return updated


Account.register_transformation(AccountInfo, Account.transform_WGAccountInfo)
