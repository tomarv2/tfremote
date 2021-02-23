import logging
from src.logging import configure_logging
logger = logging.getLogger(__name__)


def allow_list():
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
    return subcommand_pass_thru


def deny_list():
    # commands that can break setup
    blacklist_subcommand = []
    return blacklist_subcommand
