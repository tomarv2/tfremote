from __future__ import absolute_import  # isort:skip
from __future__ import print_function  # isort:skip

from ._version import __version__  # isort:skip
from src.tf_aws.plugin import TerraformAWSWrapper  # isort:skip

plugin = TerraformAWSWrapper()  # isort:skip
