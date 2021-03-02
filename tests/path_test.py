from src.common.run_command import create_command


def test_create_command():
    output = create_command(
        ["tf", "plan", "-cloud", "aws", "-var-file", "foo.vars", "-var", "foo=var"]
    )
    assert output == "tf plan -var-file foo.vars -var foo=var"

