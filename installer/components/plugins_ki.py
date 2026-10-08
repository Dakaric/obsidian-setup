from ..catalog import group_description
from .common import supported
from .plugins import apply_group, group_done, group_plan

KEY = "plugins-ki"
TITLE = "KI-Plugins"
DESCRIPTION = group_description("ki")
DEFAULT = False


def is_done(ctx):
    return group_done("ki", ctx)


def plan(ctx):
    return group_plan("ki", ctx)


def apply(ctx):
    return apply_group("ki", ctx)
