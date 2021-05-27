from src.common.run_command import (  # parse_vars,
    build_remote_backend_tf_file,
    build_tf_state_path,
    create_command,
)


def test_create_command():
    output = create_command(
        ["tf", "plan", "-cloud", "aws", "-var-file", "foo.vars", "-var", "foo=var"]
    )
    assert output == "tf plan -var-file foo.vars -var foo=var"


def test_build_remote_backend_tf_file():
    storage_type = "s3"
    workspace_key_prefix = "demo-workspace"
    fips = True
    state_key = "terraform"

    output = build_remote_backend_tf_file(
        storage_type, workspace_key_prefix, fips, state_key
    )
    assert output == True


def test_build_tf_state_path():
    required_vars = {"teamid": "hello", "prjid": "world"}
    workspace = "demo-workspace"
    state_key = "demo-key"

    var_data = {
        "inline_vars": {},
        "tfvars": {"teamid": "hello", "prjid": "world"},
        "variables_tf": {
            "aws_region": "us-west-2",
        },
    }

    output = build_tf_state_path(required_vars, var_data, state_key, workspace)
    assert output == "demo-key"


# def test_parse_vars():
#     var_data = {
#         'inline_vars': {},
#         'tfvars': {
#             'teamid': 'hello',
#             'prjid': 'world'
#         },
#         'variables_tf': {
#             'aws_region': 'us-west-2',
#         }
#     }
#
#     args = {
#         'inline_vars': {},
#         'tfvars': {
#             'teamid': 'hello',
#             'prjid': 'world'
#         },
#         'variables_tf': {
#             'aws_region': 'us-west-2',
#         }
#     }
#
#     output = parse_vars(var_data, args)
#     assert output == True
