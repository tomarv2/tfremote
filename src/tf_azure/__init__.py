from __future__ import absolute_import
from __future__ import print_function

from ._version import __version__
from src.tf_azure.plugin import TerraformAzureWrapper
plugin = TerraformAzureWrapper()
