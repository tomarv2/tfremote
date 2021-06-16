import os

from src.common.validate_allowed_workspace import allowed_workspace


def test_allowed_workspace():
    #dirname = os.path.dirname(__file__)
    dirname = (os.path.abspath(os.path.join(os.path.dirname(__file__))))#, '..', 'workspaces')))
    #workspace_file_location = os.getenv("CODEBUILD_SRC_DIR") + "/infrastructure/codebuild/workspaces.yml"
    print(dirname)
    filename = os.path.join(dirname, "../scripts/workspaces.yml")
    os.environ["TF_WORKSPACE_FILE_LOCATION"] = filename

    cloud = "aws"
    workspace = "aws-demo.us-west-2.dev"
    fips = True

    output = allowed_workspace(cloud, workspace, fips)
    assert output == ('aws-demo.us-west-2.dev', '123456789012')


# test_allowed_workspace()