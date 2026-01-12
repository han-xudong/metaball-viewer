"""
Enable `metaball_viewer.__version__` to be imported.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("metaball_viewer")
except PackageNotFoundError:
    __version__ = "unknown"
