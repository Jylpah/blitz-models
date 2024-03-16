from datetime import datetime, date
from typing import Self
from pydantic import field_validator, ConfigDict, Field, field_serializer
import logging

from pydantic_exportables import (
    CSVExportable,
    TXTExportable,
    JSONExportable,
    Importable,
    Idx,
    BackendIndex,
    IndexSortOrder,
    DESCENDING,
    ASCENDING,
)


logger = logging.getLogger()
error = logger.error
message = logger.warning
verbose = logger.info
debug = logger.debug

###########################################
#
# Release()
#
###########################################


def datetime2isodate(dt: datetime) -> str:
    return dt.date().isoformat()


def isodate2datetime(d: str) -> datetime:
    return datetime.combine(date.fromisoformat(d), datetime.min.time())


# fmt: off
class Release(JSONExportable,
                CSVExportable, 
                TXTExportable, 
                Importable):
    release     : str               = Field(default=..., alias="_id")
    launch_date : datetime | None   = Field(default=None)
    # _export_DB_by_alias			: bool = False

    _csv_custom_writers = {  "launch_date": datetime2isodate }
    _csv_custom_readers = {  "launch_date": isodate2datetime }
    model_config = ConfigDict(frozen=False, validate_assignment=True, populate_by_name=True)
# fmt: on

    @field_serializer('launch_date', when_used='json')
    def serialize_dt(self, dt: datetime | None, _info):
        if dt is None:
            return None
        else:
            return dt.date().isoformat()

    @property
    def index(self) -> Idx:
        return self.release

    @property
    def indexes(self) -> dict[str, Idx]:
        """return backend indexes"""
        return {"release": self.index}

    @classmethod
    def backend_indexes(cls) -> list[list[tuple[str, IndexSortOrder]]]:
        indexes: list[list[BackendIndex]] = list()
        indexes.append([("name", ASCENDING), ("launch_date", DESCENDING)])
        return indexes
    
 
    @classmethod
    def validate_release(cls, v: str) -> str:
        """Blitz release is format X.Y[.Z]"""
        rel: list[int] = cls._release_number(v)
        return cls._release_str(rel)


    @field_validator("release")
    @classmethod
    def _validate_release(cls, v: str) -> str:
        return cls.validate_release(v=v)


    @field_validator("launch_date", mode="before")
    @classmethod
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


    def next(self, **kwargs) -> Self:
        """Get next Blitz release version according to standard release cycle
        There are few exceptions however so this is not accurate"""
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
        return __o is not None and isinstance(__o, Release) and self.release == __o.release

    def __hash__(self) -> int:
        return hash((self.release, self.launch_date))

    def __str__(self) -> str:
        return self.release
