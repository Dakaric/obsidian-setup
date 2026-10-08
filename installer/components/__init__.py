from types import ModuleType

from . import appearance, assistant, plugins, plugins_extra, plugins_ki, settings, vault

COMPONENTS: tuple[ModuleType, ...] = (vault, assistant, appearance, plugins, plugins_extra, plugins_ki, settings)
