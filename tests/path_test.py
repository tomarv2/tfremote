from src.common.run_command import create_command
from src.common.run_command import build_remote_backend_tf_file
from src.common.run_command import build_tf_state_path
from src.common.run_command import parse_vars


def test_create_command():
    output = create_command(
        ["tf", "plan", "-cloud", "aws", "-var-file", "foo.vars", "-var", "foo=var"]
    )
    assert output == "tf plan -var-file foo.vars -var foo=var"


def test_build_remote_backend_tf_file():
    storage_type = "s3"
    output = build_remote_backend_tf_file(storage_type)
    assert output == True


def test_build_tf_state_path():
    required_vars = {
        "teamid": "hello",
        "prjid": "world"
    }

    var_data = {
        'inline_vars': {},
        'tfvars': {
            'teamid': 'hello',
            'prjid': 'world'
        },
        'variables_tf': {
            'aws_region': 'us-west-2',
        }
    }

    output = build_tf_state_path(required_vars, var_data)
    print("@" * 50)
    print(output)
    print("@" * 50)
    assert output == "terraform/hello/world/terraform.tfstate"


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
#     print(type(args))
#     print("@" * 50)
#     output = parse_vars(var_data, args)
#     print(output)
#     print("@" * 50)
#     assert output == True
