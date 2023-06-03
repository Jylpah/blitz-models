from datetime import datetime, date
from typing import Any, TypeVar, Self
from pydantic import validator, Field, HttpUrl

from pyutils import (
    CSVExportable,
    TXTExportable,
    JSONExportable,
    CSVImportable,
    TXTImportable,
    JSONImportable,
    Importable,
    Idx,
    BackendIndexType,
    BackendIndex,
)
from pyutils.exportable import DESCENDING, ASCENDING

###########################################
#
# WGBlitzRelease()
#
###########################################

# fmt: off
class WGBlitzRelease(JSONExportable, JSONImportable, 
                     CSVExportable, CSVImportable,
                     TXTExportable):
    release     : str               = Field(default=..., alias="_id")
    launch_date : datetime | None   = Field(default=None)
    # _export_DB_by_alias			: bool = False

    # fmt: on
    class Config:
        allow_mutation = True
        validate_assignment = True
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda v: v.date().isoformat()}

    @property
    def index(self) -> Idx:
        return self.release

    @property
    def indexes(self) -> dict[str, Idx]:
        """return backend indexes"""
        return {"release": self.index}

    @classmethod
    def backend_indexes(cls) -> list[list[tuple[str, BackendIndexType]]]:
        indexes: list[list[BackendIndex]] = list()
        indexes.append([("name", ASCENDING), ("launch_date", DESCENDING)])
        return indexes
    
    @validator("release")
    def validate_release(cls, v: str) -> str:
        """Blitz release is format X.Y[.Z]"""
        rel: list[int] = cls._release_number(v)
        return cls._release_str(rel)

    @validator("launch_date", pre=True)
    def validate_date(cls, d):
        if d is None:
            return None
        if isinstance(d, str):
            return datetime.combine(date.fromisoformat(d), datetime.min.time())
        elif isinstance(d, float):
            return int(d)
        elif isinstance(d, datetime):
            return datetime.combine(d.date(), datetime.min.time())
        elif isinstance(d, date):
            return datetime.combine(d, datetime.min.time())
        return d

    @classmethod
    def _release_number(cls, rel: str) -> list[int]:
        """Return release in type list[int]"""
        return [int(r) for r in rel.split(".")]

    @classmethod
    def _release_str(cls, rel: list[int]) -> str:
        """Create a release string from list[int]"""
        return ".".join([str(r) for r in rel])

    # TXTExportable()
    def txt_row(self, format: str = "") -> str:
        """export data as single row of text"""
        if format == "rich" and self.launch_date is not None:
            return f"{self.release}\t{self.launch_date.date()}"
        return self.release

    # CSVExportable()
    def csv_headers(self) -> list[str]:
        return list(self.dict(exclude_unset=False, by_alias=False).keys())

    def _csv_row(self) -> dict[str, str | int | float | bool | None ]:
        return self.dict(exclude_unset=False, by_alias=False)

    def next(self, **kwargs) -> Self:
        rel: list[int] = self._release_number(self.release)
        major: int = rel[0]
        minor: int = rel[1]
        if minor < 10:
            minor += 1
        else:
            minor = 0
            major += 1
        return type(self)(release=self._release_str([major, minor]), **kwargs)

    def __eq__(self, __o: object) -> bool:
        return __o is not None and isinstance(__o, WGBlitzRelease) and self.release == __o.release

    def __hash__(self) -> int:
        return hash((self.release, self.launch_date))

    def __str__(self) -> str:
        return self.release
