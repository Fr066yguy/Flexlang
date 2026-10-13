
import engine
from pathlib import Path
import webbrowser
import html as html_module


# Store HTML and CSS in the runtime


@engine.syntax(r'html\((.*)\)')
def html_command(match, runtime):
    content = engine.FlexRuntime.parse_value(match.group(1))
    content = runtime.interpolate(str(content))

    if not hasattr(runtime, "web_html"):
        runtime.web_html = ""

    runtime.web_html += content + "\n"


@engine.syntax(r'css\((.*)\)')
def css_command(match, runtime):
    content = engine.FlexRuntime.parse_value(match.group(1))
    content = runtime.interpolate(str(content))

    if not hasattr(runtime, "web_css"):
        runtime.web_css = ""

    runtime.web_css += content + "\n"


@engine.syntax(r'web\.save\s+"([^"]+)"')
def web_save(match, runtime):
    filename = match.group(1)

    page_html = getattr(runtime, "web_html", "")
    page_css = getattr(runtime, "web_css", "")

    document = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FlexLang Website</title>
<style>
{page_css}
</style>
</head>
<body>
{page_html}
</body>
</html>
"""

    path = Path(__file__).resolve().parent.parent / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document, encoding="utf-8")

    print(f"Website saved: {path}")


@engine.syntax(r'web\.open\s+"([^"]+)"')
def web_open(match, runtime):
    filename = match.group(1)
    path = Path(__file__).resolve().parent.parent / filename

    if not path.is_file():
        raise FileNotFoundError(
            f"Website not found: {path}. Use web.save first."
        )

    webbrowser.open(path.resolve().as_uri())
    print("Opening website in browser...")


print("FlexLang web plugin loaded!")