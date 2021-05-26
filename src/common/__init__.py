from __future__ import absolute_import  # isort:skip
from __future__ import print_function  # isort:skip

from ._version import __version__  # isort:skip
from src.common.plugin import TerraformCommonWrapper  # isort:skip

plugin = TerraformCommonWrapper()  # isort:skip
