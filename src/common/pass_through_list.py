import logging

logger = logging.getLogger(__name__)


def allow_list() -> list:
    """
    Function to list subcommands that don't need remote state
    """
    subcommand_pass_thru = [
        "fmt",
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
    ]
    return subcommand_pass_thru


def deny_list() -> list:
    """
    Function to list commands that can break setup
    """
    blacklist_subcommand = []
    return blacklist_subcommand
