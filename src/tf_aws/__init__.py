from __future__ import absolute_import, print_function
from ._version import __version__

from src.tf_aws.plugin import TerraformAWSWrapper
plugin = TerraformAWSWrapper()
