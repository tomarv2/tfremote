export TF_BASE_PATH=''

export PATH_TO_PKG=$TF_BASE_PATH'/tfremote'
export GCLOUD_BASE_DIR=$TF_BASE_PATH'/terraform/gcp/vm/base'
export AZURE_BASE_DIR=$TF_BASE_PATH'/terraform/azure/vnet/base'
export AWS_BASE_DIR=$TF_BASE_PATH'/terraform/AWS/security_group/base'
export TF_VENV=demo_env02

# Gcloud
$PATH_TO_PKG/tfremote.egg-info
rm -fr $PATH_TO_PKG/tfremote.egg-info
python3 -m venv ~/Documents/virtualenv/$TF_VENV; source ~/Documents/virtualenv/$TF_VENV/bin/activate;
cd $PATH_TO_PKG
python setup.py develop
# --
cd $GCLOUD_BASE_DIR
rm -fr .terraform; tf -cloud gcloud apply -var-file ../custom_files/sample.tfvars
rm -fr .terraform; tf destroy -var-file ../custom_files/sample.tfvars -cloud gcloud
deactivate $TF_VENV
rm -fr $TF_VENV

# Azure
$PATH_TO_PKG/tfremote.egg-info
rm -fr $PATH_TO_PKG/tfremote.egg-info
python3 -m venv ~/Documents/virtualenv/$TF_VENV; source ~/Documents/virtualenv/$TF_VENV/bin/activate
cd $PATH_TO_PKG; python setup.py develop
# --
cd $AZURE_BASE_DIR
rm -fr .terraform; tf apply -var-file ../custom_files/sample.tfvars -cloud azure
rm -fr .terraform; tf -cloud azure destroy -var-file ../custom_files/sample.tfvars
deactivate $TF_VENV
rm -fr $TF_VENV

# AWS
$PATH_TO_PKG/tfremote.egg-info
rm -fr $PATH_TO_PKG/tfremote.egg-info
python3 -m venv ~/Documents/virtualenv/$TF_VENV; source ~/Documents/virtualenv/$TF_VENV/bin/activate
cd $PATH_TO_PKG; python setup.py develop
# --
cd $AWS_BASE_DIR
rm -fr .terraform; tf apply -var-file ../custom_files/demo.tfvars -cloud aws
rm -fr .terraform; tf -cloud aws destroy -var-file ../custom_files/demo.tfvars
deactivate $TF_VENV
rm -fr $TF_VENV
