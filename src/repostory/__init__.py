"""repostory — commit analytics dashboard generator."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("repostory")
except PackageNotFoundError:
    __version__ = "0.0.0"
