from typing import Any, Optional, Self, TypeVar, Annotated
import logging
from bson.int64 import Int64
from pydantic import BaseModel, Extra, root_validator, validator, Field, HttpUrl

from pyutils import (
    CSVExportable,
    TXTExportable,
    JSONExportable,
    CSVImportable,
    TXTImportable,
    JSONImportable,
    Importable,
    TypeExcludeDict,
    Idx,
)

from .region import Region
from .wg_api import WGAccountInfo

logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug


B = TypeVar("B", bound="BaseModel")


###########################################
#
# Account()
#
###########################################

TypeAccountDict = dict[str, int | bool | Region | None]


def lateinit_region() -> Region:
    """Required for initializing a model w/o a 'region' field"""
    raise RuntimeError("should never be called")


# fmt: off
class Account(JSONExportable, JSONImportable, 
              CSVExportable, CSVImportable, 
              TXTExportable, TXTImportable, 
              Importable):
    id              : int       = Field(alias="_id")
    # lateinit is a trick to fool mypy since region is set in root_validator
    region          : Region    = Field(default_factory=lateinit_region, alias="r")
    last_battle_time: int       = Field(default=0, alias="l")
    created_at      : int       = Field(default=0, alias="c")
    updated_at      : int       = Field(default=0, alias="u")
    nickname        : str | None= Field(default=None, alias="n")
# fmt: on
    class Config:
        allow_population_by_field_name = True
        allow_mutation = True
        validate_assignment = True

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

    @validator("id")
    def check_id(cls, v):
        assert v is not None, "id cannot be None"
        assert isinstance(v, int), "id has to be int"
        if isinstance(v, Int64):
            v = int(v)
        if v < 0:
            raise ValueError("account_id must be >= 0")
        return v

    @validator("last_battle_time")
    def check_epoch_ge_zero(cls, v: int) -> int:
        if v >= 0:
            return v
        else:
            raise ValueError("time field must be >= 0")

    @root_validator(pre=True)
    def read_account_id(cls, values: TypeAccountDict) -> TypeAccountDict:
        _id = values.get("id")
        region = values.get("region")
        if region is None:
            if isinstance(_id, int):
                values["region"] = Region.from_id(_id)
            elif isinstance(_id, str):
                i, r = _id.split(":")
                values["id"] = int(i)
                values["region"] = Region(r)
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
            return cls(id=int(text), **kwargs)
        except Exception as err:
            raise ValueError(f"Could not create Account() with id={text}: {err}")

    # CSVExportable()
    def csv_headers(self) -> list[str]:
        """Provide CSV headers as list"""
        return list(self.dict(exclude_unset=False, by_alias=False).keys())

    def _csv_row(self) -> dict[str, str | int | float | bool | None]:
        """Provide instance data as dict for csv.DictWriter"""
        res: dict[str, str | int | float | bool | None ] = self.dict(exclude_unset=False, by_alias=False)
        if self.region is not None:
            res["region"] = self.region.value
        else:
            raise ValueError(f"Account {self.id} does not have region defined")
        return res

    @classmethod
    def from_str(cls, account: str) -> Self | None:
        obj: dict[str, Any] = dict()
        a = account.split(":")
        obj["id"] = int(a[0])
        if len(a) > 1:
            obj["region"] = a[1]
        return cls.parse_obj(obj)

    def __str__(self) -> str:
        fields: list[str] = [f for f in self.__fields__.keys() if f != "id"]
        return (
            f'{type(self).__name__} id={self.id}: { ", ".join( [ f + "=" + str(getattr(self,f)) for f in fields ]  ) }'
        )

    @classmethod
    def transform_WGAccountInfo(cls, in_obj: "WGAccountInfo") -> Optional["Account"]:
        """Transform WGAccountInfo object to Account"""
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

    def update(self, update: "WGAccountInfo") -> bool:
        """Update Account() from WGACcountInfo i.e. from WG API"""
        updated: bool = False
        try:
            if update.last_battle_time > 0 and self.last_battle_time != update.last_battle_time:
                self.last_battle_time = update.last_battle_time
                updated = True
            if update.created_at > 0 and update.created_at != self.created_at:
                self.created_at = update.created_at
                updated = True
            if update.updated_at > 0 and update.updated_at != self.updated_at:
                self.updated_at = update.updated_at
                updated = True
            if update.nickname is not None and (self.nickname is None or self.nickname != update.nickname):
                self.nickname = update.nickname
                updated = True
        except Exception as err:
            error(f"{err}")
        return updated


Account.register_transformation(WGAccountInfo, Account.transform_WGAccountInfo)
