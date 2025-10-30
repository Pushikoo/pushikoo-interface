__all__ = [
    # Core base types
    "Adapter",
    "AdapterClassConfig",
    "AdapterInstanceConfig",
    "AdapterFrameworkContext",
    "AdapterInfo",
    # Data result
    "GetResult",
    # Getter
    "Getter",
    "GetterClassConfig",
    "GetterInstanceConfig",
    # Pusher
    "Pusher",
    "PusherClassConfig",
    "PusherInstanceConfig",
]


import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field

from pushikoo_interface.struct import Struct

TADAPTERCLASSCONFIG = TypeVar("TADAPTERCLASSCONFIG", bound="AdapterClassConfig")
TADAPTERINSTANCECONFIG = TypeVar(
    "TADAPTERINSTANCECONFIG", bound="AdapterInstanceConfig"
)
TCONFIGSERVICETYPE = TypeVar("TCONFIGSERVICETYPE")


class AdapterInfo(BaseModel):
    version: str
    name: str
    entry: str
    type_: Literal["getter", "pusher"] = Field(alias="type", serialization_alias="type")
    author: str | None = None
    description: str | None = None
    url: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class AdapterFrameworkContext(ABC):
    info: AdapterInfo
    storage_base_path: Path

    @abstractmethod
    def get_class_config(self) -> BaseModel: ...

    @abstractmethod
    def get_instance_config(self) -> BaseModel: ...


class AdapterClassConfig(BaseModel): ...


class AdapterInstanceConfig(BaseModel): ...


class Adapter(ABC, Generic[TADAPTERCLASSCONFIG, TADAPTERINSTANCECONFIG]):
    _default_class_config_type: type
    _default_instance_config_type: type

    def __init__(self, id_: str, ctx: AdapterFrameworkContext) -> None:
        super().__init__()
        self.id = id_
        self.ctx = ctx

        self.class_name = self.ctx.info.name
        self.instance_name = self.class_name + "." + self.id

        storage_base_path = ctx.storage_base_path
        self.class_storage_path = storage_base_path / self.class_name
        self.instance_storage_path = storage_base_path / self.instance_name
        self.class_storage_path.mkdir(parents=True, exist_ok=True)
        self.instance_storage_path.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(self.instance_name)

    @property
    def config(self) -> TADAPTERCLASSCONFIG:
        return self.ctx.get_class_config()

    @property
    def instance_config(self) -> TADAPTERINSTANCECONFIG:
        return self.ctx.get_instance_config()

    def __str__(self) -> str:
        return self.instance_name

    def __hash__(self) -> int:
        return hash(self.instance_name)


class GetResult(BaseModel):
    ts: float
    content: Struct
    extra: dict


class GetterClassConfig(AdapterClassConfig): ...


class GetterInstanceConfig(AdapterInstanceConfig): ...


class Getter(
    Adapter[TADAPTERCLASSCONFIG, TADAPTERINSTANCECONFIG],
    Generic[TADAPTERCLASSCONFIG, TADAPTERINSTANCECONFIG],
):
    _default_class_config_type = GetterClassConfig
    _default_instance_config_type = GetterInstanceConfig

    @abstractmethod
    def timeline(self) -> list[str]:
        """Get newest lists. Must be overrided.

        Returns:
            list[str]: Lists of ids.
        """
        ...

    @abstractmethod
    def detail(self, id_: str | list[str]) -> GetResult:
        """Get detail of specific id or ids. Must be overrided.

        Args:
            id_: id

        Returns:
            GetResult: Result
        """
        ...


class PusherClassConfig(AdapterClassConfig): ...


class PusherInstanceConfig(AdapterInstanceConfig): ...


class Pusher(
    Adapter[TADAPTERCLASSCONFIG, TADAPTERINSTANCECONFIG],
    Generic[TADAPTERCLASSCONFIG, TADAPTERINSTANCECONFIG],
):
    _default_class_config_type = PusherClassConfig
    _default_instance_config_type = PusherInstanceConfig

    @abstractmethod
    def push(self, content: Struct) -> None: ...
