from . import ui
from .model import Context, Result


def run_component(component, ctx: Context, selected: bool) -> Result:
    support = component.supported(ctx.platform)
    print(f"\n{component.TITLE}: {component.DESCRIPTION} ({support.state})")
    if support.reason:
        print(support.reason)
    if support.state == "nein":
        return Result(component.KEY, "nicht unterstützt", support.reason)
    if component.is_done(ctx):
        return Result(component.KEY, "übersprungen", "schon eingerichtet")
    if not ui.ask_yes_no("Einrichten?", selected or component.DEFAULT, ctx):
        return Result(component.KEY, "übersprungen", "nicht gewählt")
    steps = component.plan(ctx)
    for step in steps:
        print(f"  {step}")
    if ctx.dry_run:
        return Result(component.KEY, "übersprungen", "Vorschau: " + "; ".join(steps))
    return component.apply(ctx)


def run_components(components, ctx: Context, only: set[str] | None) -> list[Result]:
    results = []
    for component in components:
        if only is not None and component.KEY not in only:
            continue
        try:
            result = run_component(component, ctx, only is not None)
        except Exception as error:
            result = Result(component.KEY, "fehler", str(error))
        results.append(result)
    return results
