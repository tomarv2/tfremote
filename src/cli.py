#!/usr/bin/env python
#
# allows team collaboration on Terraform deployments by managing centralized remote states:
# works in AWS, Azure and GCP based on teamid and prjid
#
import hcl
import re
import argparse
import sys
import json
import os
import subprocess
import logging
import shutil
import time
from typing import List
from distutils.version import StrictVersion as V

MIN_TERRAFORM_V = '0.12.0'


# function to define logging
def configure_logging():
    tf_log_level = os.getenv('TF_LOG_LEVEL')
    if tf_log_level is None:
        logging.basicConfig(level='WARNING')
    elif tf_log_level == "DEBUG":
        # log level:logged message:full module path:function invoked:line number of logging call
        log_format = "%(levelname)s:%(message)s:%(pathname)s:%(funcName)s:%(lineno)d"
        logging.basicConfig(level=tf_log_level, format=log_format)
    else:
        valid_log_levels = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']
        if tf_log_level.upper() not in valid_log_levels:
            print("ERROR: invalid log level \"%{}\".  Allowed log levels: {}"). format(
                tf_log_level, ', '.join(valid_log_levels))
            exit(1)


log = logging.getLogger(__name__)
# we configure the logging level and format
configure_logging()


# verifying version of terraform installed
def valid_terraform_version(min_supported_ver):
    cmd_output = subprocess.check_output("terraform version", shell=True)
    detected_ver = re.search(r"\d+\.\d+\.\d+", cmd_output.decode('utf-8')).group(0)
    if V(detected_ver) >= V(min_supported_ver):
        return True
    else:
        log.error("Installed terraform version: {}, is not supported by the tf wrapper script. \
        \nTerraform version must be >= {}" .format(detected_ver, min_supported_ver))
        return False


def create_command(arguments_entered: List[str]) -> str:
    cloud_providers = ['aws', 'azure', 'gcp']
    print("arguments_entered: ", arguments_entered)
    if '-cloud' in arguments_entered:
        arguments_entered.remove('-cloud')
    for i in cloud_providers:
        if i in arguments_entered:
            arguments_entered.remove(i)
    return ' '.join(arguments_entered)


class TerraformWrapper:
    var_data = {}
    args = None
    args_unknown = None
    required_vars = {"teamid": None, "prjid": None}
    logger = None
    s3_path = None
    s3_bucket = None
    s3_region = None
    aws_profile = None
    azure_path = None
    azure_stg_acc_name = None
    azure_access_key = None
    azure_container_name = None
    gcloud_path = None
    gcloud_bucket_name = None
    gcloud_credentials = None

    # following subcommands don't need remote state
    subcommand_pass_thru = ["fmt",
                            "get",
                            "graph",
                            "import",
                            "init",
                            "output",
                            "push",
                            "remote",
                            "show",
                            "taint",
                            "untaint",
                            "validate",
                            "version"
                            ]
    blacklist_subcommand = []

    def __init__(self):
        parser = argparse.ArgumentParser(description="terraform wrapper script")
        parser.add_argument('subcommand', help='terraform subcommand')
        parser.add_argument('-cloud', dest='cloud', help='specify the cloud: aws, gcloud, azure')
        parser.add_argument('-var-file', action='append', dest='tfvar_files', help='specify a tfvars file')
        parser.add_argument('-var', action='append', dest='inline_vars', help='specify a var')
        self.args, self.args_unknown = parser.parse_known_args()

    # set bucket details (get from env variables)
    def configure_aws(self):
        self.aws_profile = os.getenv('TF_AWS_PROFILE')
        self.s3_bucket = os.getenv('TF_AWS_BUCKET')
        self.s3_region = os.getenv('TF_AWS_BUCKET_REGION')
        if (self.aws_profile is None) or (self.aws_profile == ""):
            log.error("Please set the TF_AWS_PROFILE environment variable")
            exit(1)
        if (self.s3_bucket is None) or (self.s3_bucket == ""):
            log.error("Please set the TF_AWS_BUCKET environment variable")
            exit(1)
        # fixed to use 'us-west-2', to be made global
        if (self.s3_region is None) or (self.s3_region == ""):
            p = subprocess.Popen(
                ['aws', 's3api', 'get-bucket-location', '--output', 'text', '--profile', self.aws_profile, '--bucket',
                 self.s3_bucket], stdout=subprocess.PIPE)
            self.s3_region = p.communicate()[0]
            if (self.s3_region is None) or (self.s3_region == ""):
                log.error("unable to determine S3 bucket \"{}\" location.  AWS profile used is \"{}\"" .format(
                    self.s3_bucket, self.aws_profile))
                exit(1)
        log.info("[S3 bucket: {}] [AWS profile: {}] [AWS region: {}]"
                 .format(self.s3_bucket, self.aws_profile, self.s3_region))

    # set azure storage account details (get from env variables)
    def configure_azure(self):
        self.azure_container_name = os.getenv('TF_AZURE_CONTAINER')
        self.azure_stg_acc_name = os.getenv('TF_AZURE_STORAGE_ACCOUNT')
        self.azure_access_key = os.getenv('ARM_ACCESS_KEY')
        if (self.azure_container_name is None) or (self.azure_container_name == ""):
            log.error("Please set the TF_AZURE_CONTAINER environment variable")
            exit(1)
        if (self.azure_stg_acc_name is None) or (self.azure_stg_acc_name == ""):
            log.error("Please set the TF_AZURE_STORAGE_ACCOUNT environment variable")
            exit(1)
        if (self.azure_access_key is None) or (self.azure_access_key == ""):
            log.error("Unable to determine TF_AZURE_ARM_ACCESS_KEY \"{}\"" .format(self.azure_access_key))
            exit(1)
        log.info("[Azure Storage Account Name: {}] [Azure Container Name: {}]" .format(
            self.azure_stg_acc_name, self.azure_container_name))

    # set google storage account details (get from env variables)
    def configure_gcloud(self):
        self.gcloud_prefix = os.getenv('TF_GCLOUD_PREFIX')
        self.gcloud_bucket_name = os.getenv('TF_GCLOUD_BUCKET')
        self.gcloud_credentials = os.getenv('TF_GCLOUD_CREDENTIALS')
        if (self.gcloud_prefix is None) or (self.gcloud_prefix == ""):
            log.error("Please set the TF_GCLOUD_PREFIX environment variable")
            exit(1)
        if (self.gcloud_bucket_name is None) or (self.gcloud_bucket_name == ""):
            log.error("Please set the TF_GCLOUD_BUCKET environment variable")
            exit(1)
        # different credentials for different env
        if (self.gcloud_credentials is None) or (self.gcloud_credentials == ""):
            log.error("Please set the TF_GCLOUD_CREDENTIALS environment variable")
            exit(1)
        log.info("[gcloud bucket: {}] [gcloud credentials file path: {}]"
                 .format(self.gcloud_bucket_name, self.gcloud_credentials))

    def main(self):
        if vars(self.args)['subcommand'] in self.blacklist_subcommand:
            log.error("subcommand '{}' should not be used with this wrapper script as it'll break things " .format(
                vars(self.args)['subcommand']))
            exit(1)
        elif vars(self.args)['subcommand'] in self.subcommand_pass_thru:
            cmd = "terraform %s" % (' '.join(sys.argv[3:]))
            logging.debug("terraform command: {}" .format(cmd))
            ret_code = self._run_cmd(cmd)
            if ret_code == 0:
                exit(0)
            else:
                exit(1)
        else:
            if vars(self.args)['cloud'] == "aws":
                self._parse_vars()
                self.s3_path = self._build_tf_state_path()
                self.configure_aws()
                set_remote_backend_status = self._set_remote_backend()
                log.info("Remote State backend is already configured: {}" .format(set_remote_backend_status))
                if set_remote_backend_status:
                    cmd = "terraform {}" .format(create_command(sys.argv[1:]))
                    log.info("AWS command: {}" .format(cmd))
                    ret_code = self._run_cmd(cmd)
                    if ret_code == 0:
                        exit(0)
                    else:
                        exit(1)
                else:
                    raise Exception("\nThere was an error setting the remote backend for AWS; aborting")
            elif vars(self.args)['cloud'].lower() == "azure":
                self._parse_vars()
                self.azure_path = self._build_tf_state_path()
                self.configure_azure()
                set_remote_backend_status = self._set_remote_backend()
                log.info("set_remote_backend_status: {}" .format(set_remote_backend_status))
                if set_remote_backend_status:
                    cmd = "terraform {}" .format(create_command(sys.argv[1:]))
                    log.info("AZURE command: {}" .format(cmd))
                    ret_code = self._run_cmd(cmd)
                    if ret_code == 0:
                        exit(0)
                    else:
                        exit(1)
                else:
                    raise Exception("\nunable to set remote backend for Azure; aborting")
            elif vars(self.args)['cloud'] == "gcloud":
                self._parse_vars()
                self.gcloud_path = self._build_tf_state_path()
                self.configure_gcloud()
                set_remote_backend_status = self._set_remote_backend()
                log.info("set_remote_backend_status: {}" .format(set_remote_backend_status))
                if set_remote_backend_status:
                    cmd = "terraform {}".format(create_command(sys.argv[1:]))
                    log.info("GCLOUD command: {}" .format(cmd))
                    ret_code = self._run_cmd(cmd)
                    if ret_code == 0:
                        exit(0)
                    else:
                        exit(1)
                else:
                    raise Exception("\nunable to set remote backend gcloud; aborting")
            else:
                log.info("please specify the cloud provider")

    def _set_remote_backend(self):
        """
        configure the Terraform remote state if necessary
        return True if remote state was sucessfully configured
        """
        if vars(self.args)['cloud'] == "aws":
            current_tf_state = {"backend": {}}
            current_tf_state["backend"]["config"] = {}
            current_tf_state["backend"]["config"]["bucket"] = None
            current_tf_state["backend"]["config"]["key"] = None
            self._build_remote_backend_tf_file()
            if os.path.isfile(".terraform/terraform.tfstate"):
                with open(".terraform/terraform.tfstate") as fh:
                    current_tf_state = json.load(fh)
            if ("backend" in current_tf_state) and (
                    current_tf_state["backend"]["config"]["bucket"] == self.s3_bucket) and (
                    current_tf_state["backend"]["config"]["key"] == self.s3_path):
                log.debug("No need to pull remote state")
                return True
            else:
                if os.path.isfile(".terraform/terraform.tfstate"):
                    os.unlink(".terraform/terraform.tfstate")
                    log.debug("Removed .terraform/terraform.tfstate")
                cmd = "terraform init -backend-config=\"bucket={}\" -backend-config=\"region={}\" -backend-config=" \
                      "\"key={}\" -backend-config=\"acl=bucket-owner-full-control\" -backend-config=\"profile={}\"" \
                    .format(self.s3_bucket, 'us-west-2', self.s3_path, self.aws_profile)
                log.debug("init command: {}" .format(cmd))
                ret_code = self._run_cmd(cmd)
                if ret_code == 0:
                    return True
                else:
                    return False

        elif vars(self.args)['cloud'].lower() == "azure":
            current_tf_state = {"backend": {}}
            current_tf_state["backend"]["config"] = {}
            current_tf_state["backend"]["config"]["storage_account_name"] = None
            current_tf_state["backend"]["config"]["key"] = None
            self._build_remote_backend_tf_file()
            if os.path.isfile(".terraform/terraform.tfstate"):
                with open(".terraform/terraform.tfstate") as fh:
                    current_tf_state = json.load(fh)
            if ("backend" in current_tf_state) and (
                    current_tf_state["backend"]["config"]["storage_account_name"] == self.azure_stg_acc_name) and (
                    current_tf_state["backend"]["config"]["key"] == self.azure_path):
                log.debug("no need to pull remote state")
                return True
            else:
                if os.path.isfile(".terraform/terraform.tfstate"):
                    os.unlink(".terraform/terraform.tfstate")
                    log.debug("removed .terraform/terraform.tfstate")
                cmd = "terraform init -backend-config=\"storage_account_name={}\" -backend-config=\"key={}\" \
                -backend-config=\"container_name={}\"" .format(
                    self.azure_stg_acc_name, self.azure_path, self.azure_container_name)
                log.debug("init command: {}" .format(cmd))
                ret_code = self._run_cmd(cmd)
                if ret_code == 0:
                    return True
                else:
                    return False

        elif vars(self.args)['cloud'] == "gcloud":
            current_tf_state = {"backend": {}}
            current_tf_state["backend"]["config"] = {}
            current_tf_state["backend"]["config"]["bucket"] = None
            current_tf_state["backend"]["config"]["credentials"] = None
            self._build_remote_backend_tf_file()
            if os.path.isfile(".terraform/terraform.tfstate"):
                with open(".terraform/terraform.tfstate") as fh:
                    current_tf_state = json.load(fh)
            if ("backend" in current_tf_state) and (
                    current_tf_state["backend"]["config"]["bucket"] == self.gcloud_bucket_name) and (
                    current_tf_state["backend"]["config"]["credentials"] == self.gcloud_credentials):
                log.debug("no need to pull remote state")
                return True
            else:
                if os.path.isfile(".terraform/terraform.tfstate"):
                    os.unlink(".terraform/terraform.tfstate")
                    log.debug("removed .terraform/terraform.tfstate")
                cmd = "terraform init -backend-config=\"bucket={}\" -backend-config=\"credentials={}\" \
                -backend-config=\"prefix={}\"" .format(
                    self.gcloud_bucket_name, self.gcloud_credentials, self.gcloud_path)
                log.debug("init command: {}" .format(cmd))
                ret_code = self._run_cmd(cmd)
                if ret_code == 0:
                    return True
                else:
                    return False

    def _run_cmd(self, cmd):
        p = subprocess.Popen(cmd, shell=True)
        p.wait()
        return p.returncode

    def _build_remote_backend_tf_file(self):
        if os.path.exists("remote_backend.tf"):
            log.info("remote_backend.tf exists, not generating")
            return True
        else:
            if vars(self.args)['cloud'] == "aws":
                log.debug("remote_backend.tf not found, generating")
                with open('remote_backend.tf', 'w') as f:
                    f.write("# file generated by wrapper script to configure backend\n")
                    f.write("# do not edit or delete!\n")
                    f.write("\n")
                    f.write("terraform { backend \"s3\" {} }\n")
                return True
            elif vars(self.args)['cloud'] == "azure":
                log.debug("remote_backend.tf not found, generating")
                with open('remote_backend.tf', 'w') as f:
                    f.write("# file generated by wrapper script to configure backend\n")
                    f.write("# do not edit or delete!\n")
                    f.write("\n")
                    f.write("terraform { backend \"azurerm\" {} }\n")
                return True
            elif vars(self.args)['cloud'] == "gcloud":
                log.debug("remote_backend.tf not found, generating")
                with open('remote_backend.tf', 'w') as f:
                    f.write("# file generated by wrapper script to configure backend\n")
                    f.write("# do not edit or delete!\n")
                    f.write("\n")
                    f.write("terraform { backend \"gcs\" {} }\n")
                return True

    def _build_tf_state_path(self):
        for var in self.required_vars:
            if var in self.var_data["inline_vars"]:
                self.required_vars[var] = self.var_data["inline_vars"][var]
            elif var in self.var_data["tfvars"]:
                self.required_vars[var] = self.var_data["tfvars"][var]
            elif var in self.var_data["variables_tf"]:
                self.required_vars[var] = self.var_data["variables_tf"][var]
            else:
                raise Exception("ERROR: required var %s not defined" % var)
        if vars(self.args)['cloud'] == "gcloud":
            path = "terraform/%s/%s" % (self.required_vars['teamid'], self.required_vars['prjid'])
            log.debug("terraform path: %s" % path)
            return path
        else:
            path = "terraform/%s/%s/terraform.tfstate" % (self.required_vars['teamid'], self.required_vars['prjid'])
            log.debug("terraform path: %s" % path)
            return path

    def _parse_vars(self):
        # function to parse variables
        log.debug("parse variables")
        self.var_data["inline_vars"] = self._parse_inline_vars()
        self.var_data["tfvars"] = self._parse_tfvar_files()
        self.var_data["variables_tf"] = self._parse_var_file("variables.tf")
        log.debug("parsed variables: %s" % (json.dumps(self.var_data, indent=2, sort_keys=True)))

    def _parse_inline_vars(self):
        """
        parse variables defined on the commandline (-var a=b)
        """
        log.debug("parsing inline variables")
        results = {}
        if vars(self.args)['inline_vars'] is None:
            return results
        for var in vars(self.args)['inline_vars']:
            log.debug(var)
            match = re.split("\s*=\s*", var, maxsplit=1)
            key = match[0]
            value = match[1]
            results[key] = value
        return results

    def _parse_tfvar_files(self):
        # parse variables defined in terraform.tfvars and files defined in commandline (-var-file a.tfvars)
        results = {}
        tfvar_files = vars(self.args)['tfvar_files']
        if tfvar_files is None:
            log.error("please use a tfvars file to specify the customer parameters.  eg: \"-var-file custom.tfvars\"")
            exit(1)
        if (os.path.isfile('terraform.tfvars')) and ('terraform.tfvars' not in tfvar_files):
            tfvar_files.insert(0, 'terraform.tfvars')
        for file in tfvar_files:
            with open(file) as fh:
                for line in fh:
                    line = line.rstrip("\r\n")
                    line = re.sub("^\s+", "", line)
                    if re.search("^#", line) or re.search("^$", line):
                        continue
                    else:
                        match = re.split("\s*=\s*", line, maxsplit=1)
                        key = match[0]
                        value = re.sub("^\"|^'|\"$|'$", "", match[1])
                        results[key] = value
        return results

    def _parse_var_file(self, file):
        """
        parse the variables defined in .tf file
        eg:
        variable name {
            foo = "bar"
        }
        """
        results = {}
        with open(file) as fh:
            data = hcl.load(fh)
        for var in data["variable"]:
            if "default" in data["variable"][var]:
                results[var] = data["variable"][var]["default"]
        return results


def entrypoint():
    if not valid_terraform_version(MIN_TERRAFORM_V):
        exit(1)
    else:
        TerraformWrapper().main()


if __name__ == "__main__":
    entrypoint()
