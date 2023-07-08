import logging
import json
from warnings import warn
from typing import Any, Optional, Self
from enum import IntEnum, StrEnum
from pydantic import root_validator, validator, Field, Extra, ValidationError
from aiofiles import open
from pyutils.jsonexportable import Idx
from sortedcollections import SortedDict  # type: ignore
from re import Pattern, compile, match

from pyutils import (
    CSVExportable,
    TXTExportable,
    JSONExportable,
    TXTImportable,
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


class MapMode(IntEnum):
    training = 0
    normal = 1
    special = 2
    partial = 3


class Map(JSONExportable):
    key: str = Field(default=..., alias="_id")
    name: str = Field(default=..., alias="n")
    id: int = Field(default=-1)
    mode: MapMode = Field(default=MapMode.normal, alias="m")

    _exclude_unset = False
    _exclude_defaults = False

    # _re_partial_name: Pattern = compile(r" - ")
    _re_partial_key: Pattern = compile(r'_\d{2}$')  # fmt: skip

    @root_validator(pre=False)
    def _map_mode(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Set map's type/mode"""
        key: str = values["key"]
        if cls._re_partial_key.search(key):
            values["mode"] = MapMode.partial
        elif key in {"test", "moon", "iceworld", "Wasteland"}:
            values["mode"] = MapMode.special
        elif key in {"tutorial"}:
            values["mode"] = MapMode.training
        return values

    class Config:
        allow_mutation = True
        validate_assignment = True
        allow_population_by_field_name = True

    @property
    def index(self) -> Idx:
        return self.key


class Maps(JSONExportable):
    __root__: SortedDict[str, Map] = SortedDict()

    _exclude_unset = False
    _exclude_defaults = False

    class Config:
        allow_mutation = True
        validate_assignment = True
        allow_population_by_field_name = True

    # @root_validator(pre=True)
    # def _import_dict(cls, values: dict[str, Any]) -> dict[str, Map]:
    #     res: dict[str, Map] = dict()
    #     maps = values["__root__"]
    #     for key, value in maps.items():
    #         try:
    #             res[key] = Map.parse_obj(value)
    #             continue
    #         except ValidationError:
    #             debug(f"could not parse Map() from: {value}")
    #         try:
    #             res[key] = Map(key=key, name=value)
    #             debug(f"new Map(key={key}, name={value})")
    #         except Exception as err:
    #             error(f"could not validate key={key}, map={value}")
    #         values["__root__"] = res
    #     return values

    # @validator("__root__", pre=True)
    # def _import_data(cls, value: dict[str, Any]) -> SortedDict[str, Map]:
    #     res: SortedDict[str, Map] = SortedDict()
    #     for key, val in value.items():
    #         try:
    #             res[key] = Map.parse_obj(val)
    #             continue
    #         except ValidationError:
    #             debug(f"could not parse Map() from: {val}")
    #         try:
    #             res[key] = Map(key=key, name=val)
    #             debug(f"new Map(key={key}, name={val})")
    #         except Exception as err:
    #             error(f"could not validate key={key}, map={val}: {err}")
    #     return res

    @validator("__root__", pre=False)
    def _ensure_sorteddict(cls, value) -> SortedDict[str, Map]:
        if not isinstance(value, SortedDict):
            return SortedDict(**value)

    @classmethod
    async def open_json(cls, filename: str) -> Self | None:
        """Open replay JSON file and return class instance"""
        if (res := await super().open_json(filename)) is None:
            warn("legacy JSON format is depreciated", category=DeprecationWarning)
            try:
                res = cls()
                async with open(filename, "r", encoding="utf8") as f:
                    objs: dict[str, Any] = json.loads(await f.read())
                    for key, obj in objs.items():
                        try:
                            res.add(Map(key=key, name=obj))
                            debug(f"new Map(key={key}, name={obj})")
                        except Exception as err:
                            debug(f"could not validate key={key}, map={obj}: {err}")
                return res
            except Exception as err:
                debug(f"Error reading: {err}")
            return None
        return res

    def __iter__(self):
        return iter(self.__root__)

    def __getitem__(self, key) -> Map:
        return self.__root__[key]

    def __setitem__(self, key: str, map: Map) -> None:
        self.__root__[key] = map

    def __len__(self) -> int:
        return len(self.__root__)

    def add(self, map: str | Map, key: str | None = None):
        if isinstance(map, str):
            if isinstance(key, str):
                map = Map(key=key, name=map)
            else:
                raise ValueError("map name and key given, but key is not a string")
        self.__root__[map.key] = map

    def update(self, new: "Maps") -> None:
        """update Maps with another Maps instance"""
        self.__root__.update(new.__root__)
