from importlib.metadata import distribution, packages_distributions
from typing import Callable, Generic, TypeVar


TPropertyValue = TypeVar("T")


class classproperty(Generic[TPropertyValue]):
    def __init__(self, func: Callable[[type], TPropertyValue]) -> None:
        self.func = func

    def __get__(self, instance: object, owner: type) -> TPropertyValue:
        return self.func(owner)


def get_dist_meta(class_: type):
    """
    Retrieve distribution information for the current module.

    Returns:
        tuple: A tuple containing the distribution name, version, and metadata dictionary.
        Returns None if the distribution cannot be determined.
    """
    mod_name = class_.__module__.split(".")[0]

    dist_name = packages_distributions().get(mod_name, [None])[0]
    if dist_name is None:
        return None

    dist = distribution(dist_name)
    return dist.name, dist.version, dist.metadata
