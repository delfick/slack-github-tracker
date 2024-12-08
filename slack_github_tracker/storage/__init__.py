import importlib

from ._metadata import metadata

importlib.import_module("._prs", package=__name__)

__all__ = ["metadata"]
