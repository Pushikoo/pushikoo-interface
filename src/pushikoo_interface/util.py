from importlib.metadata import (
    Distribution,
    distribution,
    distributions,
    packages_distributions,
)
from typing import Callable, Generic, TypeVar

TPropertyValue = TypeVar("T")


class classproperty(Generic[TPropertyValue]):
    def __init__(self, func: Callable[[type], TPropertyValue]) -> None:
        self.func = func

    def __get__(self, instance: object, owner: type) -> TPropertyValue:
        return self.func(owner)


def _get_dist(module: str) -> Distribution | None:
    """
    Locate a distribution by inspecting its entry points and matching
    the top-level import package against `module`.
    """
    for dist in distributions():
        try:
            for ep in dist.entry_points:
                # ep.value: "pkg.module:object"
                value = ep.value

                if ":" not in value:
                    continue

                module_path, _ = value.split(":", 1)
                top_level = module_path.split(".", 1)[0]

                if top_level == module:
                    return dist

        except Exception:
            # entry_points Failure to parse should not affect the overall scan
            continue

    return None


def get_dist_meta(class_: type):
    """
    Retrieve distribution information for the current module.

    Returns:
        tuple: A tuple containing the distribution name, version, and metadata dictionary.
        Returns None if the distribution cannot be determined.
    """
    mod_name = class_.__module__.split(".")[0]

    dist_name = packages_distributions().get(mod_name, [None])[0]
    if dist_name is not None:
        dist = distribution(dist_name)
        return dist.name, dist.version, dist.metadata

    if (dist := _get_dist(mod_name)) is not None:
        return dist.name, dist.version, dist.metadata

    return None, None, None
