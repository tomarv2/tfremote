from __future__ import absolute_import  # isort:skip
from __future__ import print_function  # isort:skip

from ._version import __version__  # isort:skip
from src.tf_azure.plugin import TerraformAzureWrapper  # isort:skip

plugin = TerraformAzureWrapper()  # isort:skip
