
import os
import sys
import shutil
import subprocess
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEATURES = ROOT / "features"
ENGINE = ROOT / "engine.py"
STUDIO = ROOT / "studio.py"
PLATFORMER = FEATURES / "platformer.py"

passed = 0
failed = 0
warnings = 0


def report(name, ok, details=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"[PASS] {name}")
    else:
        failed += 1
        print(f"[FAIL] {name}")
    if details:
        print(f"       {details}")


def warn(name, details):
    global warnings
    warnings += 1
    print(f"[CHECK MANUALLY] {name}")
    print(f"       {details}")


def check_file(path, label):
    report(label, path.is_file(), str(path))


def compile_file(path):
    if not path.is_file():
        return False, "File not found"
    try:
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")
        return True, "Python syntax is valid"
    except Exception as error:
        return False, str(error)


def run_script(command, label, expected_text=None, timeout=20):
    try:
        result = subprocess.run(
            command,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=(os.name == "nt"),
        )

        output = (result.stdout or "") + "\n" + (result.stderr or "")

        if result.returncode != 0:
            report(
                label, False,
                f"Exit code: {result.returncode}\n"
                + output[-1800:]
            )
            return False

        if expected_text and expected_text not in output:
            report(
                label, False,
                f"Expected output not found: {expected_text!r}\n"
                + output[-1800:]
            )
            return False

        report(label, True, f"Exit code: {result.returncode}")
        return True

    except subprocess.TimeoutExpired:
        report(label, False, f"Timed out after {timeout} seconds.")
        return False
    except Exception as error:
        report(label, False, str(error))
        return False


def main():
    global passed, failed, warnings

    print("=" * 58)
    print(" FLEXGAME STUDIO V2 — FULL SYSTEM SELF-TEST")
    print("=" * 58)
    print(f"Project: {ROOT}")
    print(f"Python:  {sys.version.split()[0]}")
    print()

    # 1. Core files
    print("--- CORE FILES ---")
    check_file(ENGINE, "FlexLang engine exists")
    check_file(STUDIO, "FlexGame Studio exists")
    check_file(FEATURES, "Features folder exists")
    check_file(PLATFORMER, "Platformer plugin exists")

    if not ENGINE.is_file() or not FEATURES.is_dir():
        print("\nCannot continue: core files are missing.")
        return

    # 2. Dependencies
    print("\n--- DEPENDENCIES ---")
    for module_name in ("customtkinter", "pygame"):
        try:
            spec = importlib.util.find_spec(module_name)
            report(
                f"{module_name} is installed",
                spec is not None,
            )
        except Exception as error:
            report(f"{module_name} is installed", False, str(error))

    # 3. Python syntax
    print("\n--- PYTHON SYNTAX ---")
    files_to_compile = [ENGINE, STUDIO, PLATFORMER]
    files_to_compile += sorted(FEATURES.glob("*.py"))

    seen = set()
    for path in files_to_compile:
        if path in seen:
            continue
        seen.add(path)
        ok, detail = compile_file(path)
        report(f"Syntax: {path.relative_to(ROOT)}", ok, detail)

    # 4. Plugin inventory
    print("\n--- PLUGIN INVENTORY ---")
    plugins = sorted(FEATURES.glob("*.py"))
    report("At least one plugin exists", bool(plugins))
    for plugin in plugins:
        print(f"       Plugin: {plugin.name}")

    # 5. flxrun command
    print("\n--- TERMINAL COMMAND ---")
    flxrun = shutil.which("flxrun")
    report(
        "flxrun is on PATH",
        flxrun is not None,
        flxrun or "Open a new terminal or rerun your PATH setup script."
    )

    # 6. Run a simple FlexLang program
    print("\n--- FLEX LANG EXECUTION ---")
    test_script = ROOT / "_flexgame_selftest.flx"

    source = (
        "--mutestart\n"
        'say "FLEXGAME_SELFTEST_OK"\n'
        "create score set 0\n"
        "score = score + 10\n"
        'say "FlexGame test score: {score}"\n'
    )

    try:
        test_script.write_text(source, encoding="utf-8")

        run_script(
            [sys.executable, str(ENGINE), str(test_script)],
            "Engine runs a .flx script",
            "FLEXGAME_SELFTEST_OK",
        )

        # Check actual variable interpolation and math result.
        run_script(
            [sys.executable, str(ENGINE), str(test_script)],
            "Create, math, and say work together",
            "FlexGame test score: 10",
        )

        # 7. Check flxrun wrapper, if available.
        if flxrun:
            command = f'flxrun "{test_script}"'
            run_script(
                command,
                "flxrun launches a .flx script",
                "FLEXGAME_SELFTEST_OK",
            )

        # 8. Check platformer plugin commands without opening a game.
        print("\n--- PLATFORMER PLUGIN ---")
        platformer_script = ROOT / "_flexgame_platformer_test.flx"
        platformer_source = (
            "--mutestart\n"
            'platformer.window 800 450\n'
            'platformer.background "#182438"\n'
            'platformer.player 50 50 32 42 "#4da6ff"\n'
            'platformer.platform 0 410 800 40 "#36b36a"\n'
            'platformer.coin 350 350 24 "#ffd447"\n'
            'platformer.enemy 530 378 32 32 "#ff5964"\n'
            'say "PLATFORMER_SETUP_OK"\n'
        )

        platformer_script.write_text(
            platformer_source, encoding="utf-8"
        )

        run_script(
            [sys.executable, str(ENGINE), str(platformer_script)],
            "Platformer setup commands are accepted",
            "PLATFORMER_SETUP_OK",
        )

        platformer_script.unlink(missing_ok=True)

    finally:
        test_script.unlink(missing_ok=True)

    # 9. Check whether the GUI can initialize.
    print("\n--- GUI ---")
    if importlib.util.find_spec("customtkinter") is None:
        report("GUI dependencies available", False)
    else:
        warn(
            "Studio opens and displays correctly",
            "Launch with: py studio.py. Verify the scene canvas, "
            "buttons, inspector, and console visually."
        )

    warn(
        "Scene save/open and drag-and-drop",
        "In the GUI, move an object, save the scene, open it again, "
        "and confirm the object's position is preserved."
    )

    warn(
        "Actual gameplay",
        "Press RUN, save the exported .flx file, and test movement, "
        "jumping, platform collisions, coin collection, enemy contact, "
        "restart, and closing the game."
    )

    # 10. Results
    print("\n" + "=" * 58)
    print(" TEST RESULTS")
    print("=" * 58)
    print(f"Passed:          {passed}")
    print(f"Failed:          {failed}")
    print(f"Manual checks:   {warnings}")
    print()

    if failed == 0:
        print("AUTOMATED CHECKS PASSED.")
        print("Complete the manual checks to verify the GUI and gameplay.")
    else:
        print("SOME CHECKS FAILED.")
        print("Fix the first failure, then run this test again.")

    print("=" * 58)


if __name__ == "__main__":
    main()