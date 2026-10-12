
import os
import sys
import queue
import threading
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk


# ============================================================
# FLEXGAME STUDIO v1
# GUI editor for the existing FlexLang engine
# ============================================================

ROOT = Path(__file__).resolve().parent
ENGINE = ROOT / "engine.py"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class FlexGameStudio(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("FlexGame Studio")
        self.geometry("1250x800")
        self.minsize(900, 600)

        self.current_file = None
        self.process = None
        self.output_queue = queue.Queue()
        self.dirty = False

        self.configure(fg_color="#11151d")

        self.build_ui()
        self.refresh_files()
        self.new_file()
        self.after(75, self.read_output_queue)
        self.protocol("WM_DELETE_WINDOW", self.close_app)

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def build_ui(self):
        header = ctk.CTkFrame(self, corner_radius=0, fg_color="#192230")
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="🎮 FlexGame Studio",
            font=("Segoe UI", 23, "bold"),
            text_color="#69b7ff",
        ).pack(side="left", padx=18, pady=12)

        self.status_label = ctk.CTkLabel(
            header,
            text="Ready",
            text_color="#a9b6c9",
        )
        self.status_label.pack(side="right", padx=18)

        toolbar = ctk.CTkFrame(self, corner_radius=0, fg_color="#202b3b")
        toolbar.pack(fill="x")

        self.tool_button(toolbar, "New", self.new_file)
        self.tool_button(toolbar, "Open", self.open_file)
        self.tool_button(toolbar, "Save", self.save_file)
        self.tool_button(toolbar, "Save As", self.save_as)
        self.tool_button(toolbar, "Refresh Files", self.refresh_files)

        ctk.CTkFrame(
            toolbar, width=2, height=26, fg_color="#46536a"
        ).pack(side="left", padx=7, pady=8)

        ctk.CTkButton(
            toolbar,
            text="▶  RUN",
            width=100,
            fg_color="#16834b",
            hover_color="#20a65f",
            command=self.run_game,
        ).pack(side="left", padx=5, pady=7)

        ctk.CTkButton(
            toolbar,
            text="■  STOP",
            width=100,
            fg_color="#a73542",
            hover_color="#c44553",
            command=self.stop_game,
        ).pack(side="left", padx=5, pady=7)

        main = ctk.CTkFrame(self, corner_radius=0, fg_color="#11151d")
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # Left: project browser
        left = ctk.CTkFrame(main, width=220, fg_color="#192230")
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        ctk.CTkLabel(
            left,
            text="PROJECT FILES",
            font=("Segoe UI", 12, "bold"),
            text_color="#8dbdf5",
        ).pack(anchor="w", padx=12, pady=(12, 5))

        self.file_list = tk.Listbox(
            left,
            bg="#192230",
            fg="#e1e8f2",
            selectbackground="#285a89",
            selectforeground="white",
            relief="flat",
            borderwidth=0,
            font=("Consolas", 10),
            activestyle="dotbox",
        )
        self.file_list.pack(fill="both", expand=True, padx=6, pady=6)
        self.file_list.bind("<Double-Button-1>", self.open_selected_file)

        ctk.CTkLabel(
            left,
            text="Double-click a .flx file",
            font=("Segoe UI", 10),
            text_color="#8998ad",
        ).pack(padx=8, pady=(0, 10))

        # Center: code editor
        center = ctk.CTkFrame(main, fg_color="#11151d")
        center.pack(side="left", fill="both", expand=True)

        self.file_label = ctk.CTkLabel(
            center,
            text="Untitled.flx",
            anchor="w",
            font=("Segoe UI", 13, "bold"),
            text_color="#dce8f8",
        )
        self.file_label.pack(fill="x", padx=6, pady=(0, 6))

        editor_frame = ctk.CTkFrame(center, fg_color="#0d1118")
        editor_frame.pack(fill="both", expand=True)

        self.editor = tk.Text(
            editor_frame,
            wrap="none",
            undo=True,
            bg="#0d1118",
            fg="#e4eaf3",
            insertbackground="white",
            selectbackground="#264d73",
            font=("Consolas", 12),
            relief="flat",
            padx=12,
            pady=12,
            tabs=("32p",),
        )

        editor_scroll_y = tk.Scrollbar(
            editor_frame, command=self.editor.yview
        )
        editor_scroll_x = tk.Scrollbar(
            editor_frame,
            orient="horizontal",
            command=self.editor.xview,
        )
        self.editor.configure(
            yscrollcommand=editor_scroll_y.set,
            xscrollcommand=editor_scroll_x.set,
        )

        editor_scroll_y.pack(side="right", fill="y")
        editor_scroll_x.pack(side="bottom", fill="x")
        self.editor.pack(fill="both", expand=True)

        self.editor.bind("<<Modified>>", self.editor_modified)
        self.editor.bind("<Control-s>", self.save_shortcut)
        self.editor.bind("<Control-Return>", self.run_shortcut)

        # Right: useful snippets
        right = ctk.CTkFrame(main, width=175, fg_color="#192230")
        right.pack(side="right", fill="y", padx=(8, 0))
        right.pack_propagate(False)

        ctk.CTkLabel(
            right,
            text="CODE SNIPPETS",
            font=("Segoe UI", 12, "bold"),
            text_color="#8dbdf5",
        ).pack(anchor="w", padx=10, pady=(12, 8))

        snippets = [
            ("Say text", 'say "Hello, world!"'),
            ("Create variable", "create score set 0"),
            ("Add numbers", "score = score + 10"),
            ("If / else", 'if score > 10\n    say "You win!"\nelse\n    say "Keep going!"\nend'),
            ("Random number", "random number 1 to 100"),
            ("Wait 1 second", "sleep 1"),
            ("Game window", 'window.new "My Game" 800 600'),
        ]

        for label, code in snippets:
            ctk.CTkButton(
                right,
                text=label,
                anchor="w",
                fg_color="#26364a",
                hover_color="#345071",
                command=lambda snippet=code: self.insert_snippet(snippet),
            ).pack(fill="x", padx=8, pady=3)

        ctk.CTkLabel(
            right,
            text="SHORTCUTS",
            font=("Segoe UI", 11, "bold"),
            text_color="#8dbdf5",
        ).pack(anchor="w", padx=10, pady=(20, 5))

        ctk.CTkLabel(
            right,
            text="Ctrl + S  Save\nCtrl + Enter  Run",
            justify="left",
            text_color="#aab8ca",
        ).pack(anchor="w", padx=10)

        # Bottom: output console
        console = ctk.CTkFrame(self, fg_color="#192230")
        console.pack(fill="x", padx=10, pady=(0, 10))

        console_header = ctk.CTkFrame(console, fg_color="transparent")
        console_header.pack(fill="x", padx=8, pady=(6, 2))

        ctk.CTkLabel(
            console_header,
            text="OUTPUT CONSOLE",
            font=("Segoe UI", 12, "bold"),
            text_color="#8dbdf5",
        ).pack(side="left")

        ctk.CTkButton(
            console_header,
            text="Clear",
            width=60,
            height=24,
            command=self.clear_console,
        ).pack(side="right")

        self.output = ctk.CTkTextbox(
            console,
            height=145,
            font=("Consolas", 11),
            fg_color="#0d1118",
            text_color="#d6e2f1",
            wrap="word",
        )
        self.output.pack(fill="x", padx=8, pady=(2, 8))
        self.log("FlexGame Studio ready.")
        self.log(f"Engine: {ENGINE}")

    def tool_button(self, parent, text, command):
        ctk.CTkButton(
            parent,
            text=text,
            width=78,
            command=command,
            fg_color="#34445b",
            hover_color="#465b78",
        ).pack(side="left", padx=4, pady=7)

    # --------------------------------------------------------
    # Editor and files
    # --------------------------------------------------------

    def editor_modified(self, _event=None):
        if self.editor.edit_modified():
            self.dirty = True
            self.editor.edit_modified(False)
            self.update_file_label()

    def update_file_label(self):
        name = self.current_file.name if self.current_file else "Untitled.flx"
        self.file_label.configure(
            text=name + ("  *" if self.dirty else "")
        )

    def confirm_discard(self):
        if not self.dirty:
            return True

        answer = messagebox.askyesnocancel(
            "Unsaved changes",
            "Save your changes before continuing?",
        )

        if answer is None:
            return False
        if answer:
            return self.save_file()
        return True

    def new_file(self):
        if not self.confirm_discard():
            return

        self.current_file = None
        self.editor.delete("1.0", "end")
        self.editor.insert(
            "1.0",
            '# My first FlexLang program\n'
            'say "Welcome to FlexGame Studio!"\n'
            'say "Edit this file, save it, then press RUN."\n',
        )
        self.dirty = False
        self.editor.edit_modified(False)
        self.update_file_label()
        self.status_label.configure(text="New file")
        self.editor.focus_set()

    def open_file(self):
        if not self.confirm_discard():
            return

        filename = filedialog.askopenfilename(
            title="Open FlexLang script",
            initialdir=str(ROOT),
            filetypes=[
                ("FlexLang scripts", "*.flx"),
                ("All files", "*.*"),
            ],
        )
        if filename:
            self.load_file(Path(filename))

    def open_selected_file(self, _event=None):
        selection = self.file_list.curselection()
        if not selection:
            return

        relative_path = self.file_list.get(selection[0])
        path = ROOT / relative_path

        if path.is_file() and not self.confirm_discard():
            return
        if path.is_file():
            self.load_file(path)

    def load_file(self, path):
        try:
            source = path.read_text(encoding="utf-8")
        except Exception as error:
            messagebox.showerror("Open failed", str(error))
            return

        self.current_file = path
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", source)
        self.editor.edit_modified(False)
        self.dirty = False
        self.update_file_label()
        self.status_label.configure(text="Opened")
        self.editor.focus_set()

    def save_file(self):
        if self.current_file is None:
            return self.save_as()

        try:
            self.current_file.parent.mkdir(parents=True, exist_ok=True)
            self.current_file.write_text(
                self.editor.get("1.0", "end-1c"),
                encoding="utf-8",
            )
            self.dirty = False
            self.editor.edit_modified(False)
            self.update_file_label()
            self.refresh_files()
            self.status_label.configure(text="Saved")
            return True
        except Exception as error:
            messagebox.showerror("Save failed", str(error))
            return False

    def save_as(self):
        filename = filedialog.asksaveasfilename(
            title="Save FlexLang script",
            initialdir=str(ROOT),
            defaultextension=".flx",
            filetypes=[("FlexLang scripts", "*.flx")],
        )
        if not filename:
            return False

        self.current_file = Path(filename)
        return self.save_file()

    def save_shortcut(self, _event=None):
        self.save_file()
        return "break"

    def refresh_files(self):
        self.file_list.delete(0, "end")
        try:
            files = sorted(
                p for p in ROOT.rglob("*.flx")
                if "__pycache__" not in p.parts
                and ".git" not in p.parts
            )
            for path in files:
                self.file_list.insert("end", str(path.relative_to(ROOT)))
        except Exception as error:
            self.log(f"File browser error: {error}")

    def insert_snippet(self, snippet):
        self.editor.insert("insert", snippet + "\n")
        self.editor.focus_set()
        self.dirty = True
        self.update_file_label()

    # --------------------------------------------------------
    # Run and stop
    # --------------------------------------------------------

    def run_shortcut(self, _event=None):
        self.run_game()
        return "break"

    def run_game(self):
        if not ENGINE.is_file():
            messagebox.showerror(
                "Engine not found",
                f"Could not find engine.py here:\n{ENGINE}",
            )
            return

        if not self.save_file():
            return

        if self.process and self.process.poll() is None:
            messagebox.showwarning(
                "Already running",
                "Stop the current script before starting another.",
            )
            return

        self.clear_console()
        self.log(f"Running: {self.current_file}")
        self.status_label.configure(text="Running...")

        try:
            self.process = subprocess.Popen(
                [
                    sys.executable,
                    str(ENGINE),
                    str(self.current_file),
                ],
                cwd=str(ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=None,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except Exception as error:
            self.log(f"Could not start FlexLang: {error}")
            self.status_label.configure(text="Launch failed")
            return

        threading.Thread(
            target=self.read_process,
            args=(self.process,),
            daemon=True,
        ).start()

    def read_process(self, process):
        try:
            if process.stdout:
                for line in process.stdout:
                    self.output_queue.put(("line", line))
            code = process.wait()
            self.output_queue.put(("exit", code))
        except Exception as error:
            self.output_queue.put(("line", f"Output error: {error}\n"))

    def read_output_queue(self):
        try:
            while True:
                kind, value = self.output_queue.get_nowait()
                if kind == "line":
                    self.log(value.rstrip("\n"))
                elif kind == "exit":
                    self.status_label.configure(
                        text=f"Finished (exit code {value})"
                    )
                    self.log(f"Process finished with exit code {value}.")
                    self.process = None
        except queue.Empty:
            pass

        self.after(75, self.read_output_queue)

    def stop_game(self):
        if self.process and self.process.poll() is None:
            self.log("Stopping FlexLang...")
            try:
                self.process.terminate()
            except Exception as error:
                self.log(f"Stop error: {error}")
            self.status_label.configure(text="Stopping...")
        else:
            self.status_label.configure(text="Ready")

    # --------------------------------------------------------
    # Console and exit
    # --------------------------------------------------------

    def log(self, message):
        self.output.insert("end", str(message) + "\n")
        self.output.see("end")

    def clear_console(self):
        self.output.delete("1.0", "end")

    def close_app(self):
        if not self.confirm_discard():
            return

        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
            except Exception:
                pass

        self.destroy()


if __name__ == "__main__":
    if not ENGINE.is_file():
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "FlexLang not found",
            "Put studio.py in your Flexlang folder beside engine.py.",
        )
        root.destroy()
        raise SystemExit(1)

    app = FlexGameStudio()
    app.mainloop()