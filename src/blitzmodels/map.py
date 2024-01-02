import logging
import json
from warnings import warn
from typing import Any, Self
from enum import IntEnum, StrEnum
from pydantic import (
    model_validator,
    ConfigDict,
    Field,
    ValidationError,
)
from aiofiles import open
from pathlib import Path

from re import Pattern, compile

from pydantic_exportables import (
    JSONExportable,
    JSONExportableRootDict,
    Idx,
)

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

    @property
    def toMapModeStr(self) -> "MapModeStr":
        """Convert to MapModeStr"""
        return MapModeStr[self.name]


class MapModeStr(StrEnum):
    training = "training"
    normal = "normal"
    special = "special"
    partial = "partial"

    @property
    def toMapMode(self) -> MapMode:
        """Convert to MapMode"""
        return MapMode[self.name]


class Map(JSONExportable):
    key: str = Field(default=..., alias="_id")
    name: str = Field(default=..., alias="n")
    id: int = Field(default=-1)
    mode: MapMode = Field(default=MapMode.normal, alias="m")

    _exclude_unset = False
    _exclude_defaults = False

    # _re_partial_name: Pattern = compile(r" - ")
    _re_partial_key: Pattern = compile(r'_\d{2}$')  # fmt: skip

    @model_validator(mode="after")
    def _map_mode(self) -> Self:
        """Set map's type/mode"""
        if self.mode != MapMode.normal:
            return self
        if self._re_partial_key.search(self.key):
            self.mode = MapMode.partial
        elif self.key in {"test", "moon", "iceworld", "Wasteland"}:
            self.mode = MapMode.special
        elif self.key in {"tutorial"}:
            self.mode = MapMode.training
        return self

    model_config = ConfigDict(
        frozen=False, validate_assignment=True, populate_by_name=True
    )

    @property
    def index(self) -> Idx:
        return self.key


class Maps(JSONExportableRootDict[Map]):
    """Container model for Maps"""

    _exclude_unset = False
    _exclude_defaults = False
    model_config = ConfigDict(
        frozen=False,
        validate_assignment=True,
        populate_by_name=True,
        from_attributes=True,
    )

    @classmethod
    async def open_json(
        cls, filename: Path | str, exceptions: bool = False
    ) -> Self | None:
        """Open replay JSON file and return class instance"""
        if (
            res := await super().open_json(filename, exceptions=exceptions)
        ) is not None:
            return res
        else:
            warn("legacy JSON format is depreciated", category=DeprecationWarning)
            try:
                res = cls()
                async with open(filename, "r", encoding="utf8") as f:
                    objs: dict[str, Any] = json.loads(await f.read())
                    for key, obj in objs.items():
                        try:
                            res.add(Map(key=key, name=obj))
                            debug(f"new Map(key={key}, name={obj})")
                        except ValidationError as err:
                            debug(f"could not validate key={key}, map={obj}: {err}")
                return res
            except OSError as err:
                debug(f"Error reading file: {filename}: {err}")
            except ValidationError as err:
                debug(f"Error parsing file: {filename}: {err}")
            return None

    # def update_maps(self, new: "Maps") -> Tuple[set[str], set[str]]:
    #     """update Maps with another Maps instance"""
    #     # self.__root__.update(new.__root__)

    #     new_keys: set[str] = {map.key for map in new}
    #     old_keys: set[str] = {map.key for map in self}
    #     added: set[str] = new_keys - old_keys
    #     updated: set[str] = new_keys & old_keys

    #     self.root.update({(key, new[key]) for key in added})

    #     updated = {key for key in updated if new[key] != self[key]}
    #     updated_ids: set[str] = set()
    #     for key in updated:
    #         if self[key].update(new[key]):
    #             updated_ids.add(key)
    #     return (added, updated)
