import logging

logger = logging.getLogger(__name__)


def allow_list():
    """
    Following subcommands don't need remote state
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


def deny_list():
    """
    Commands that can break setup
    """
    blacklist_subcommand = []
    return blacklist_subcommand
