from ..catalog import group_description
from .common import supported
from .plugins import apply_group, group_done, group_plan

KEY = "plugins-extra"
TITLE = "Zusätzliche Plugins"
DESCRIPTION = group_description("extra")
DEFAULT = False


def is_done(ctx):
    return group_done("extra", ctx)


def plan(ctx):
    return group_plan("extra", ctx)


def apply(ctx):
    return apply_group("extra", ctx)
