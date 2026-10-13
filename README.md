# FlexLang

**A flexible, plugin-powered programming language built with Python.**

FlexLang is a programming language designed around readable syntax, extensibility, and custom features. Its plugin architecture allows developers to add new language capabilities without constantly modifying the core engine.

Write simple scripts, perform calculations, work with variables and lists, handle errors, import other FlexLang files, and experiment with building games and tools.

## ✨ Features

* **Readable syntax** — write code in a straightforward, beginner-friendly style.
* **Plugin architecture** — add language features through Python plugins.
* **Variables** — create and store values.
* **Math operations** — perform arithmetic calculations.
* **Text output** — display messages and variable values.
* **Conditions** — compare values and use conditional logic.
* **Lists** — store and manage collections of values.
* **Error handling** — experiment with `try` and `catch` blocks.
* **File imports** — reuse code from other `.flx` files.
* **Additional features** — extend the language with custom plugins.
* **Python-powered** — built using Python.

*Features may depend on which plugins are installed and enabled.*

## 🚀 Example

Here is a simple FlexLang program:

```flexlang
create player set "FlexLang"
create score set 10

score = score + 32

say "Welcome, {player}!"
say "Your score is {score}"
```

Example output:

```text
Welcome, FlexLang!
score = 42
Your score is 42
```

## 📦 Requirements

* Windows, or another platform supported by your Python setup
* Python 3
* Any additional dependencies required by the plugins you use

Some optional features may require additional Python packages.

## 🛠️ Installation

### 1. Install Python

Download Python from:

https://www.python.org/downloads/

On Windows, make sure Python is available through the `py` command.

### 2. Download FlexLang

Clone the repository:

```powershell
git clone 
```

Alternatively, download the repository as a ZIP file from GitHub and extract it.

### 3. Open the project folder

```powershell
cd FlexLang https://github.com/Fr066yguy/Flexlang/edit/main/README.md
```

### 4. Run a FlexLang script

If you have configured the `flxrun` launcher, run:

```powershell
flxrun example.flx
```

Or run the engine directly:

```powershell
py engine.py C:path\to\the\script
```

Replace `example.flx` with the path to your own FlexLang script.

## 📁 Project Structure

```text
FlexLang/
├── engine.py
├── studio.py
├── selftest.py
├── FLEXLANG_GUIDE.txt
├── features/
│   ├── create.py
│   ├── math.py
│   ├── say.py
│   ├── compare.py
│   ├── if_else.py
│   ├── lists.py
│   ├── a_try_catch.py
│   └── a_import.py
├── examples/
│   └── example.flx
├── README.md
├── LICENSE
└── .gitignore
```

*The exact files and folders may change as FlexLang develops. Keep the structure in this example aligned with the actual repository.*

## 🧩 The Plugin System

FlexLang uses Python files in the `features/` folder to add language functionality.

A feature plugin can register syntax with the engine, allowing the language to recognize new instructions without requiring every feature to be built directly into the core.

For example, a plugin can introduce a new instruction for displaying text, creating variables, handling lists, or implementing a custom tool.

### Creating a Plugin

1. Open the `features/` directory.
2. Create a new Python file.
3. Import the engine.
4. Register a syntax pattern and implement its handler.
5. Restart FlexLang and test the new syntax.

Example plugin structure:

```python
import engine

@engine.syntax(r"hello")
def hello_feature(match, runtime):
    print("Hello from a FlexLang plugin!")
```

Save it as `features/hello.py`, then run a FlexLang script containing:

```flexlang
hello
```

This is a minimal example. More advanced plugins may need additional validation and error handling.

## 📚 Language Examples

### Variables

```flexlang
create name set "Alex"
create level set 12

say "Player: {name}"
say "Level: {level}"
```

### Math

```flexlang
create result set 10
result = result + 5
result = result * 2

say "Result: {result}"
```

### Lists

```flexlang
list.create inventory
list.add inventory "Iron"
list.add inventory "Copper"
list.show inventory
```

### Error Handling

```flexlang
try
    say "Running protected code"
catch error
    say "Something went wrong: {error}"
end
```

### Importing Files

Suppose `helper.flx` contains:

```flexlang
say "Hello from the helper file!"
create bonus set 32
```

Another script can import it:

```flexlang
import "helper.flx"
say "Bonus: {bonus}"
```

Imported files must follow the import restrictions implemented by the current engine and plugin.

## 🎮 Experiments and Projects

FlexLang can be extended for experiments such as:

* Small games
* Text-based adventures
* Calculators
* Automation scripts
* Custom commands and syntax
* Game-development experiments
* Reusable code libraries

These are possible project directions, not a guarantee that every capability is already implemented.

## 🧪 Testing

Run the self-test script from the project directory:

```powershell
py selftest.py
```

You can also create `.flx` files to test language features individually.

## 🗺️ Roadmap

Planned or potential future improvements:

* [ ] More built-in data structures
* [ ] Improved error messages
* [ ] Better debugging tools
* [ ] Expanded standard library
* [ ] More reusable modules
* [ ] Improved development environment
* [ ] More game-development features
* [ ] Comprehensive language documentation

## 🤝 Contributions and Redistribution

FlexLang uses a custom, restrictive license.

Viewing, studying, and modifying the source code are permitted only within the conditions described in the `LICENSE` file. Redistribution of the original or modified FlexLang source code requires prior written permission from the copyright holder.

Please read the `LICENSE` file before using or modifying this project.

## 📜 License

FlexLang is distributed under its own custom license.

See [`LICENSE`](LICENSE) for the full terms.

This is a custom restrictive license, not an OSI-approved open-source license.

## 👨‍💻 About

FlexLang is an evolving programming language project focused on readable syntax and a modular, plugin-based design.

**Built with Python. Extended with plugins. Made to evolve.**
