from __future__ import absolute_import  # isort:skip
from __future__ import print_function  # isort:skip

from ._version import __version__  # isort:skip
from src.tf_gcloud.plugin import TerraformGcloudWrapper  # isort:skip

plugin = TerraformGcloudWrapper()  # isort:skip
