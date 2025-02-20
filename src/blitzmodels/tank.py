import logging
from typing import Any, ClassVar
from enum import IntEnum, StrEnum
from pydantic import field_validator, ConfigDict, Field
import re

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

from .types import TankId

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


_str_type_mapping: dict[str, str] = {
    "lt": "lightTank",
    "light": "lightTank",
    "lighttank": "lightTank",
    "mt": "mediumTank",
    "med": "mediumTank",
    "medium": "mediumTank",
    "mediumtank": "mediumTank",
    "ht": "heavyTank",
    "heavy": "heavyTank",
    "heavytank": "heavyTank",
    "td": "AT-SPG",
    "tankdestroyer": "AT-SPG",
}


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

    @classmethod
    def from_str(cls, s: str) -> "EnumVehicleTypeStr":
        try:
            s = re.sub("[_-]", "", s.lower())
            return EnumVehicleTypeStr(_str_type_mapping[s])
        except (IndexError, ValueError):
            raise ValueError(f"could not map {s} to a tank type")


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
    tank_id 	: TankId			= Field(default=..., alias = '_id')
    name   		: str 				= Field(default="")
    code        : str | None        = Field(default=None)
    nation   	: EnumNation  		= Field(default=EnumNation.european)
    type 	  	: EnumVehicleTypeStr= Field(default=EnumVehicleTypeStr.heavy_tank)
    tier 		: EnumVehicleTier 	= Field(default=EnumVehicleTier.I)
    is_premium 	: bool 				= Field(default=False)


    _example: ClassVar[str] = """{
                                    "_id": 2849,
                                    "name": "T34",
                                    "code": "T34_hvy",
                                    "nation": 2,
                                    "type": "mediumTank",
                                    "tier": 8,
                                    "is_premium": true
                                }"""
    # fmt: on
    model_config = ConfigDict(
        validate_assignment=True, populate_by_name=True, extra="allow"
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
        indexes.append([("name", TEXT), ("code", TEXT)])
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

    _txt_row_format_rich: ClassVar[str] = "{:<5} {:<4} {:<15} {:<8} {}"
    _txt_row_format: ClassVar[str] = "{:<5} {}"

    def txt_row(self, format: str = "") -> str:
        """export data as a single row of text"""
        if format == "rich":
            return self._txt_row_format_rich.format(
                *[
                    str(s)
                    for s in [
                        self.tank_id,
                        self.tier,
                        self.type,
                        self.nation,
                        self.name,
                    ]
                ]
            )
            # return f"({str(self.tank_id) + ')':<6} tier {str(self.tier):<4} {str(self.type):<15} {str(self.nation):<8} {self.name}"
        else:
            return self._txt_row_format.format(
                *[str(s) for s in [self.tank_id, self.name]]
            )

    @classmethod
    def txt_header(cls, format: str = "") -> str:
        """export header for txt file"""
        if format == "rich":
            return cls._txt_row_format_rich.format(
                *["Id", "Tier", "Type", "Nation", "Name"]
            )
        else:
            return cls._txt_row_format.format(*["Id", "Name"])

    # def update(self, new: "Tank") -> bool:
    #     """update Tank with a new info"""
    #     if self.tank_id != new.tank_id:
    #         error(f"tank_ids do not match: {self.tank_id} != {new.tank_id}")
    #         return False
    #     updated: bool = False
    #     for name, info in new.model_fields.items():
    #         new_value: Any = getattr(new, name)
    #         if new_value != info.get_default():
    #             self._set_skip_validation(name, new_value)
    #             updated = True
    #     return updated
