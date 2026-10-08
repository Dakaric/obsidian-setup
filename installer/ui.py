from .model import Context, Result


def ask_yes_no(question: str, default: bool, ctx: Context) -> bool:
    if ctx.assume_yes:
        return default
    choices = "J/n" if default else "j/N"
    while True:
        answer = input(f"{question} [{choices}] ").strip().lower()
        if not answer:
            return default
        if answer in ("j", "ja", "y", "yes"):
            return True
        if answer in ("n", "nein", "no"):
            return False
        print("Bitte ja oder nein eingeben.")


def ask_text(question: str, default: str, ctx: Context) -> str:
    if ctx.assume_yes:
        return default
    return input(f"{question} [{default}]: ").strip() or default


def print_summary(results: list[Result]) -> None:
    print("\nErgebnis:")
    for result in results:
        print(f"  {result.key}: {result.status}. {result.detail}")
    next_steps = dict.fromkeys(step for result in results for step in result.next_steps)
    if next_steps:
        print("\nNächste Schritte:")
        for number, step in enumerate(next_steps, 1):
            print(f"  {number}. {step}")
