import logging
from typing import Any, ClassVar
from enum import IntEnum, StrEnum
from pydantic import field_validator, ConfigDict, Field

from pydantic_exportables import (
    CSVExportable,
    TXTExportable,
    JSONExportable,
    Idx,
    IndexSortOrder,
    BackendIndex,
    ASCENDING,
    TEXT,
)

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
    I 		= 1   # noqa: E741
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

    @classmethod
    def _missing_(cls, value):
        try:
            return cls[value]
        except Exception as err:
            error(err)
        return None

    def __str__(self) -> str:
        if self.value in [0, 2, 5]:
            return f"{self.name}".upper()
        else:
            return f"{self.name}".capitalize()


class Tank(JSONExportable, CSVExportable, TXTExportable):
    # fmt: off
    tank_id 	: int 						= Field(default=..., alias = '_id')
    name   		: str | None				= Field(default=None)
    code        : str | None                 = Field(default=None)
    nation   	: EnumNation | None	 		= Field(default=None)
    type 	  	: EnumVehicleTypeStr| None	= Field(default=None)
    tier 		: EnumVehicleTier| None 	= Field(default=None)
    is_premium 	: bool 						= Field(default=False)


    _example: ClassVar[str] = """{
                                    "_id": 2849,
                                    "name": "T34",
                                    "nation": 2,
                                    "type": "mediumTank",
                                    "tier": 8,
                                    "is_premium": true
                                }"""
    # fmt: on
    model_config = ConfigDict(
        frozen=False, validate_assignment=True, populate_by_name=True, extra="allow"
    )

    @property
    def index(self) -> Idx:
        """return backend index"""
        return self.tank_id

    @property
    def indexes(self) -> dict[str, Idx]:
        """return backend indexes"""
        return {"tank_id": self.index}

    @classmethod
    def backend_indexes(cls) -> list[list[tuple[str, IndexSortOrder]]]:
        indexes: list[list[BackendIndex]] = list()
        indexes.append([("tier", ASCENDING), ("type", ASCENDING)])
        indexes.append([("tier", ASCENDING), ("nation", ASCENDING)])
        indexes.append([("name", TEXT)])
        return indexes

    @field_validator("tank_id")
    @classmethod
    def validate_id(cls, v: int) -> int:
        if v > 0:
            return v
        raise ValueError("id must be > 0")

    @field_validator("nation", mode="before")
    @classmethod
    def validate_nation(cls, v: Any) -> Any:
        if isinstance(v, str):
            return EnumNation[v].value
        else:
            return v

    def txt_row(self, format: str = "") -> str:
        """export data as single row of text"""
        if format == "rich":
            return f"({self.tank_id}) {self.name} tier {self.tier} {self.type} {self.nation}"
        else:
            return f"({self.tank_id}) {self.name}"
