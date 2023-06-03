import logging
import json
from warnings import warn
from typing import Any, Optional
from enum import IntEnum, StrEnum
from pydantic import root_validator, validator, Field, Extra

from pyutils import (
    CSVExportable,
    TXTExportable,
    JSONExportable,
    CSVImportable,
    TXTImportable,
    JSONImportable,
    Idx,
    BackendIndexType,
    BackendIndex,
)
from pyutils.exportable import DESCENDING, ASCENDING, TEXT

logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug


class EnumVehicleTypeInt(IntEnum):
    # fmt: off
    light_tank 	    = 0
    medium_tank     = 1
    heavy_tank 	    = 2
    tank_destroyer  = 3
    # fmt: on

    def __str__(self) -> str:
        return f"{self.name}".replace("_", " ").capitalize()

    @property
    def as_str(self) -> "EnumVehicleTypeStr":
        return EnumVehicleTypeStr[self.name]

    @classmethod
    def from_str(cls, t: str) -> "EnumVehicleTypeInt":
        return EnumVehicleTypeStr(t).as_int


class EnumVehicleTypeStr(StrEnum):
    # fmt: off
    light_tank 		= 'lightTank'
    medium_tank 	= 'mediumTank'
    heavy_tank 		= 'heavyTank'
    tank_destroyer	= 'AT-SPG'
    # fmt: on

    def __str__(self) -> str:
        return f"{self.name}".replace("_", " ").capitalize()

    @property
    def as_int(self) -> "EnumVehicleTypeInt":
        return EnumVehicleTypeInt[self.name]

    @classmethod
    def from_int(cls, t: int) -> "EnumVehicleTypeStr":
        return EnumVehicleTypeInt(t).as_str


class EnumVehicleTier(IntEnum):
    # fmt: off
    I 		= 1
    II 		= 2
    III 	= 3
    IV 		= 4
    V 		= 5
    VI 		= 6
    VII 	= 7
    VIII 	= 8
    IX 		= 9
    X		= 10
    # fmt: on

    def __str__(self) -> str:
        return str(self.name)

    @classmethod
    def read_tier(cls, tier: str) -> "EnumVehicleTier":
        try:
            if tier.isdigit():
                return EnumVehicleTier(int(tier))
            else:
                return EnumVehicleTier[tier]
        except Exception as err:
            raise ValueError(f"incorrect tier: '{tier}': {err}")


class EnumNation(IntEnum):
    # fmt: off
    ussr		= 0
    germany		= 1
    usa 		= 2
    china 		= 3
    france		= 4
    uk			= 5
    japan		= 6
    other		= 7
    european	= 8
    # fmt: on

    def __str__(self) -> str:
        if self.value in [0, 2, 5]:
            return f"{self.name}".upper()
        else:
            return f"{self.name}".capitalize()


class WGTank(JSONExportable, JSONImportable):
    # fmt: off
    tank_id 	: int 						= Field(default=..., alias = '_id')
    name   		: str | None				= Field(default=None)
    nation   	: EnumNation | None	 		= Field(default=None)
    type 	  	: EnumVehicleTypeStr| None	= Field(default=None)
    tier 		: EnumVehicleTier| None 	= Field(default=None)
    is_premium 	: bool 						= Field(default=False)
    # fmt: on

    class Config:
        allow_mutation = True
        validate_assignment = True
        allow_population_by_field_name = True
        extra = Extra.allow

    @property
    def index(self) -> Idx:
        """return backend index"""
        return self.tank_id

    @property
    def indexes(self) -> dict[str, Idx]:
        """return backend indexes"""
        return {"tank_id": self.index}

    @classmethod
    def backend_indexes(cls) -> list[list[tuple[str, BackendIndexType]]]:
        indexes: list[list[BackendIndex]] = list()
        indexes.append([("tier", ASCENDING), ("type", ASCENDING)])
        indexes.append([("tier", ASCENDING), ("nation", ASCENDING)])
        indexes.append([("name", TEXT)])
        return indexes

    @validator("tank_id")
    def validate_id(cls, v: int) -> int:
        if v > 0:
            return v
        raise ValueError("id must be > 0")

    @validator("nation", pre=True)
    def validate_nation(cls, v: Any) -> Any:
        if isinstance(v, str):
            return EnumNation[v].value
        else:
            return v
