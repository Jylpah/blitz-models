import logging

# import json
# from warnings import warn
from typing import List, ClassVar, Self, Dict, Optional
from enum import IntEnum, StrEnum
from pydantic import (
    # model_validator,
    ConfigDict,
    Field,
    # ValidationError,
)
import aiofiles
from pathlib import Path
from re import Pattern, compile, Match
from yaml import safe_load  # type: ignore
from importlib.resources.abc import Traversable
from importlib.resources import as_file
import importlib

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
    # fmt: off
    id:     int             = Field(default=..., alias="_id")
    key:    str             = Field(default=..., alias="k")
    name:   str             = Field(default="", alias="n")
    localization_code: str  = Field(default="", alias="lc")
    modes:  List[MapMode]   = Field(default_factory=list, alias="m")
    # fmt: on
    _exclude_unset = False
    _exclude_defaults = False

    # _re_partial_name: Pattern = compile(r" - ")
    # _re_partial_key: Pattern = compile(r'_\d{2}$')  # fmt: skip
    _re_localization: ClassVar[Pattern] = compile(r"^#maps:(\w+):(.+?\/.+)$")

    # @model_validator(mode="after")
    # def _map_mode(self) -> Self:
    #     """Set map's type/mode"""
    #     if self.mode != MapMode.normal:
    #         return self
    #     if self._re_partial_key.search(self.key):
    #         self.mode = MapMode.partial
    #     elif self.key in {"test", "moon", "iceworld", "Wasteland"}:
    #         self.mode = MapMode.special
    #     elif self.key in {"tutorial"}:
    #         self.mode = MapMode.training
    #     return self

    model_config = ConfigDict(
        frozen=False, validate_assignment=True, populate_by_name=True
    )

    def read_localization_str(self, localization: str) -> bool:
        """
        Read 'key' and 'localization_code' from Blitz localization string
        """
        match: Match | None
        if (
            (match := self._re_localization.match(localization)) is None
            or (key := match.group(1)) is None
            or (loc_code := match.group(2)) is None
        ):
            return False
        self._set_skip_validation("key", key)
        self._set_skip_validation("localization_code", loc_code)
        return True

    @property
    def index(self) -> Idx:
        return self.id


class Maps(JSONExportableRootDict[int, Map]):
    """Container model for Maps"""

    _exclude_unset = False
    _exclude_defaults = False

    _re_localization: ClassVar[Pattern] = compile(r"^#maps:(\w+):(.+?\/.+)$")

    model_config = ConfigDict(
        frozen=False,
        validate_assignment=True,
        populate_by_name=True,
        from_attributes=True,
    )

    @classmethod
    async def open_yaml(
        cls, filename: Path | str, exceptions: bool = False
    ) -> Self | None:
        """
        Read Maps from Blitz game maps.yaml file
        """
        try:
            async with aiofiles.open(file=filename, mode="r", encoding="utf-8") as file:
                debug(f"yaml file opened: {str(filename)}")
                return cls.load_yaml(await file.read())
        except OSError as err:
            debug(f"Error reading file: {filename}: {err}")
        return None

    @classmethod
    def load_yaml(cls, yaml_doc: str) -> Self | None:
        """
        Read Maps from Blitz game maps.yaml input
        """
        try:
            maps: Self = cls()
            maps_yaml = safe_load(yaml_doc)
            for key, map_cfg in maps_yaml["maps"].items():
                try:
                    map_id: int = int(map_cfg["id"])
                    modes: List[int] = map_cfg["availableModes"]
                    localization_code: str = map_cfg["localName"]
                    maps.add(
                        Map(
                            id=map_id,
                            key=key,
                            modes=modes,
                            localization_code=localization_code,
                        )
                    )
                except KeyError as err:
                    error(f"could not read map config for map_key={key}: {err}")
            if len(maps) > 0:
                return maps
        except KeyError:
            error("no YAML root key 'maps' found in input")
        return None

    @classmethod
    def default_path(cls) -> Path:
        """
        Return Path of the Tankopedia shipped with the package
        """
        packaged_maps: Traversable = importlib.resources.files("blitzmodels").joinpath(
            "maps.json"
        )  # REFACTOR in Python 3.12
        with as_file(packaged_maps) as maps_fn:
            return maps_fn

    @classmethod
    def open_default(cls) -> Optional[Self]:
        """
        Open maps shipped with the package
        """
        with open(cls.default_path(), "r", encoding="utf-8") as file:
            return cls.parse_str(file.read())

    def get_by_key(self, key: str) -> Map | None:
        """A brute-force map search by key"""
        for map in self.root.values():
            if map.key == key:
                return map
        return None

    def add_names(self, localization_strs: Dict[str, str]) -> int:
        """Update maps from Blitz game localization strings 'en.yaml'"""
        updated: int = 0
        names: Dict[str, str] = dict()

        for loc_key, name in localization_strs.items():
            # some Halloween map variants have the same short name
            if (
                (match := self._re_localization.match(loc_key))
                and (key := match.group(1))
                and (loc_str := match.group(2))
            ):
                names[f"{key}:{loc_str}"] = name

        for map in self.root.values():
            try:
                map.name = names[f"{map.key}:{map.localization_code}"]
                updated += 1
            except KeyError:
                debug(f"no name found for map id={map.id}, key={map.key}")
        return updated

    # @classmethod
    # async def open_json(
    #     cls, filename: Path | str, exceptions: bool = False
    # ) -> Self | None:
    #     """Open replay JSON file and return class instance"""
    #     if (
    #         res := await super().open_json(filename, exceptions=exceptions)
    #     ) is not None:
    #         return res
    #     else:
    #         warn("legacy JSON format is depreciated", category=DeprecationWarning)
    #         try:
    #             res = cls()
    #             async with aiofiles.open(filename, "r", encoding="utf8") as f:
    #                 objs: dict[str, Any] = json.loads(await f.read())
    #                 for key, obj in objs.items():
    #                     try:
    #                         res.add(Map(key=key, name=obj))
    #                         debug(f"new Map(key={key}, name={obj})")
    #                     except ValidationError as err:
    #                         debug(f"could not validate key={key}, map={obj}: {err}")
    #             return res
    #         except OSError as err:
    #             debug(f"Error reading file: {filename}: {err}")
    #         except ValidationError as err:
    #             debug(f"Error parsing file: {filename}: {err}")
    #         return None

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
