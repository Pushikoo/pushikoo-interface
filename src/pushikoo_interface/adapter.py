import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from pushikoo_interface import util
from pushikoo_interface.structure import Struct

TADAPTERCLASSCONFIG = TypeVar("TADAPTERCLASSCONFIG", bound="AdapterClassConfig")
TADAPTERINSTANCECONFIG = TypeVar(
    "TADAPTERINSTANCECONFIG", bound="AdapterInstanceConfig"
)


class AdapterMeta(BaseModel):
    name: str
    version: str
    author: str | None = None
    description: str | None = None
    url: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class AdapterFrameworkContext(ABC):
    storage_base_path: Path
    proxies: dict[str, str]

    @abstractmethod
    def get_class_config(self) -> BaseModel: ...

    @abstractmethod
    def get_instance_config(self) -> BaseModel: ...


class AdapterClassConfig(BaseModel): ...


class AdapterInstanceConfig(BaseModel): ...


class Adapter(ABC, Generic[TADAPTERCLASSCONFIG, TADAPTERINSTANCECONFIG]):
    _default_class_config_type: type
    _default_instance_config_type: type

    id_: str
    ctx: AdapterFrameworkContext
    meta: AdapterMeta
    class_name: str
    instance_name: str
    class_storage_path: Path
    instance_storage_path: Path
    logger: logging.Logger

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)

        obj.id_ = kwargs.pop("id_", None)
        obj.ctx = kwargs.pop("ctx", None)

        dist_name, dist_version, dist_metadata = util.get_dist_meta(obj.__class__)

        url = dist_metadata.get("Home-page")
        if url is None:
            url: str | None = dist_metadata.get("Project-URL", [None])[0]
            if url:
                url = url.split(",", 1)[1].strip()

        obj.meta = AdapterMeta(
            name=dist_name,
            version=dist_version,
            author=dist_metadata.get("Author"),
            description=dist_metadata.get("Summary")
            or dist_metadata.get("Description"),
            url=url,
            extra={
                k: v
                for k, v in dist_metadata.items()
                if k not in {"Name", "Version", "Summary", "Author", "Home-page"}
            },
        )

        if obj.ctx is None or obj.id_ is None:
            raise ValueError("Adapter requires both ctx and id_ to be provided")

        obj.class_name = obj.meta.name
        obj.instance_name = f"{obj.class_name}.{obj.id_}"

        storage_base_path = obj.ctx.storage_base_path
        obj.class_storage_path = storage_base_path / obj.class_name
        obj.instance_storage_path = storage_base_path / obj.instance_name
        obj.class_storage_path.mkdir(parents=True, exist_ok=True)
        obj.instance_storage_path.mkdir(parents=True, exist_ok=True)

        obj.logger = logging.getLogger(obj.instance_name)

        return obj

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


class Detail(BaseModel):
    model_config = ConfigDict(keyword_only=True)

    ts: float = Field(description="10-digit integer Unix timestamp (decimals allowed)")
    content: str | Struct = Field(description="Main content payload")

    title: str | None = Field(
        default=None, description="Title or headline of the content"
    )
    author_id: str | None = Field(
        default=None, description="Unique identifier of the author"
    )
    author_name: str | None = Field(
        default=None, description="Display name of the author"
    )
    url: str | list[str] = Field(
        default_factory=list, description="Primary or related URLs for the content"
    )
    image: list[str] = Field(
        default_factory=list, description="Image URLs associated with the content"
    )
    extra_detail: list[str] = Field(
        default_factory=list,
        description="Structured detailed data for content representation",
    )

    detail: dict = Field(
        default_factory=dict,
        description="Additional descriptive text or metadata details for message",
    )


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
    def detail(self, id_: str) -> Detail:
        """Get detail of a specific id. Must be overrided.

        Args:
            id_: id

        Returns:
            GetResult: Result
        """
        ...

    def details(self, ids: list[str]) -> Detail:
        """Get detail of specific ids as a single Detail.

        Args:
            id_: id

        Returns:
            GetResult: Result
        """
        raise NotImplementedError()


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
