
import engine


# ==========================================
# FLEX LANG: MUTED STARTUP
# ==========================================

@engine.source_handler
def mute_startup(source, runtime, run_lines):
    lines = source.splitlines()

    # Check whether the script enables muted startup.
    muted = any(
        line.strip().lower() == "--mutestart"
        for line in lines
    )

    if not muted:
        return False

    # Remove the startup directive and run the rest.
    cleaned_lines = [
        line for line in lines
        if line.strip().lower() != "--mutestart"
    ]

    run_lines("\n".join(cleaned_lines))
    return True


print("FlexLang mute-start plugin loaded!")