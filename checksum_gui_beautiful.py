#!/usr/bin/env python3
"""
Checksum Generator / Verifier (tkinter only)
"""

import hashlib
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from queue import Queue

BUFFER_SIZE = 1024 * 1024
ALGORITHMS = ["md5", "sha1", "sha224", "sha256", "sha384", "sha512", "blake2b", "blake2s"]

# ---------- Colours & Fonts ----------
BG_COLOR = "#f0f2f5"
FRAME_BG = "#ffffff"
PRIMARY = "#4a6fa5"
ACCENT = "#3c5a7d"
TEXT_COLOR = "#333333"
SUCCESS_COLOR = "#2e7d32"
FAIL_COLOR = "#c62828"
FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
TITLE_FONT = ("Segoe UI", 14, "bold")


class BeautifulChecksumApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Checksum Tool")
        self.root.geometry("680x460")
        self.root.minsize(640, 400)
        self.root.configure(bg=BG_COLOR)

        # Use a clean ttk style
        self.style = ttk.Style()
        self._configure_styles()

        # Main container with a slight margin
        main_frame = tk.Frame(root, bg=BG_COLOR)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Header
        header = tk.Label(main_frame, text="Checksum Generator & Verifier",
                          font=TITLE_FONT, bg=BG_COLOR, fg=PRIMARY)
        header.pack(pady=(0, 15))

        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)

        self.generate_tab = tk.Frame(self.notebook, bg=FRAME_BG)
        self.verify_tab = tk.Frame(self.notebook, bg=FRAME_BG)
        self.notebook.add(self.generate_tab, text="  Generate  ")
        self.notebook.add(self.verify_tab, text="  Verify  ")

        self._build_generate_tab()
        self._build_verify_tab()

        # Threading
        self._progress_queue = Queue()
        self._running = False

    def _configure_styles(self):
        """Custom ttk styles for a modern look."""
        self.style.theme_use("clam")

        # Configure the notebook tabs
        self.style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=FRAME_BG, font=FONT_BOLD,
                             padding=[20, 6], foreground=TEXT_COLOR)
        self.style.map("TNotebook.Tab", background=[("selected", PRIMARY)],
                       foreground=[("selected", "white")])

        # Buttons
        self.style.configure("Primary.TButton", font=FONT_BOLD, background=PRIMARY,
                             foreground="white", borderwidth=0, padding=8)
        self.style.map("Primary.TButton",
                       background=[("active", ACCENT), ("disabled", "#cccccc")],
                       foreground=[("disabled", "#666666")])

        self.style.configure("Secondary.TButton", font=FONT,
                             background=FRAME_BG, foreground=PRIMARY,
                             borderwidth=1, relief="solid", padding=6)
        self.style.map("Secondary.TButton",
                       background=[("active", "#e8ecf1")])

        # Labels
        self.style.configure("TLabel", background=FRAME_BG, font=FONT, foreground=TEXT_COLOR)
        self.style.configure("Header.TLabel", font=TITLE_FONT, background=BG_COLOR,
                             foreground=PRIMARY)

        # Entry fields
        self.style.configure("TEntry", fieldbackground=FRAME_BG, font=FONT, padding=6)

        # Progress bar
        self.style.configure("TProgressbar", thickness=8, troughcolor="#e0e0e0",
                             background=PRIMARY)

        # Frames
        self.style.configure("Card.TFrame", background=FRAME_BG, relief="flat", borderwidth=0)

    # ---------- Generate Tab ----------
    def _build_generate_tab(self):
        # Outer padding using a tk.Frame for background colour
        tab = self.generate_tab
        tab.columnconfigure(0, weight=1)

        card = tk.Frame(tab, bg=FRAME_BG, padx=25, pady=25)
        card.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        card.columnconfigure(1, weight=1)

        # File selection
        tk.Label(card, text="Select file", font=FONT_BOLD, bg=FRAME_BG, fg=TEXT_COLOR).grid(
            row=0, column=0, sticky="w", pady=(0, 2))
        file_frame = tk.Frame(card, bg=FRAME_BG)
        file_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=45)
        file_entry.pack(side="left", fill="x", expand=True)
        browse_btn = ttk.Button(file_frame, text="Browse", style="Secondary.TButton",
                                command=self._browse_file)
        browse_btn.pack(side="left", padx=(10, 0))

        # Algorithm
        tk.Label(card, text="Algorithm", font=FONT_BOLD, bg=FRAME_BG, fg=TEXT_COLOR).grid(
            row=2, column=0, sticky="w", pady=(0, 2))
        algo_frame = tk.Frame(card, bg=FRAME_BG)
        algo_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        self.algo_var = tk.StringVar(value="sha256")
        algo_combo = ttk.Combobox(algo_frame, textvariable=self.algo_var,
                                  values=ALGORITHMS, state="readonly", font=FONT, width=20)
        algo_combo.pack(side="left")

        # Progress bar
        self.gen_progress = ttk.Progressbar(card, orient="horizontal",
                                            mode="determinate", length=300)
        self.gen_progress.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 5))

        # Generate button
        self.gen_button = ttk.Button(card, text="Generate Checksum",
                                     style="Primary.TButton", command=self._start_generate)
        self.gen_button.grid(row=5, column=0, columnspan=2, pady=15)

        # Hash output area
        result_frame = tk.Frame(card, bg=FRAME_BG)
        result_frame.grid(row=6, column=0, columnspan=2, sticky="ew")
        result_frame.columnconfigure(0, weight=1)

        tk.Label(result_frame, text="Checksum", font=FONT_BOLD, bg=FRAME_BG,
                 fg=TEXT_COLOR).grid(row=0, column=0, sticky="w", pady=(0, 2))
        hash_input_frame = tk.Frame(result_frame, bg=FRAME_BG)
        hash_input_frame.grid(row=1, column=0, sticky="ew")
        hash_input_frame.columnconfigure(0, weight=1)

        self.hash_var = tk.StringVar()
        hash_entry = ttk.Entry(hash_input_frame, textvariable=self.hash_var,
                               state="readonly", font=("Consolas", 9))
        hash_entry.grid(row=0, column=0, sticky="ew")

        self.copy_button = ttk.Button(hash_input_frame, text="Copy",
                                      style="Secondary.TButton",
                                      command=self._copy_hash, state="disabled")
        self.copy_button.grid(row=0, column=1, padx=(10, 0))

    def _browse_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.file_path_var.set(path)

    def _start_generate(self):
        file_path = self.file_path_var.get().strip()
        if not file_path or not Path(file_path).exists():
            messagebox.showwarning("Missing File", "Please select a valid file.")
            return

        self.gen_button.config(state="disabled")
        self.gen_progress["value"] = 0
        self.hash_var.set("")
        self.copy_button.config(state="disabled")

        self._running = True
        algo = self.algo_var.get()
        thread = threading.Thread(target=self._generate_worker,
                                  args=(Path(file_path), algo), daemon=True)
        thread.start()
        self._poll_progress("generate")

    def _generate_worker(self, file_path, algo):
        try:
            file_size = file_path.stat().st_size
            hash_func = hashlib.new(algo)
            bytes_read = 0
            with open(file_path, "rb") as f:
                while self._running:
                    chunk = f.read(BUFFER_SIZE)
                    if not chunk:
                        break
                    hash_func.update(chunk)
                    bytes_read += len(chunk)
                    percent = min(int(bytes_read / file_size * 100), 100) if file_size else 100
                    self._progress_queue.put(("progress", percent))
            self._progress_queue.put(("done", hash_func.hexdigest()))
        except Exception as e:
            self._progress_queue.put(("error", str(e)))
        finally:
            self._running = False

    # ---------- Verify Tab ----------
    def _build_verify_tab(self):
        tab = self.verify_tab
        tab.columnconfigure(0, weight=1)

        card = tk.Frame(tab, bg=FRAME_BG, padx=25, pady=25)
        card.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        card.columnconfigure(1, weight=1)

        # File
        tk.Label(card, text="Select file", font=FONT_BOLD, bg=FRAME_BG, fg=TEXT_COLOR).grid(
            row=0, column=0, sticky="w", pady=(0, 2))
        file_frame = tk.Frame(card, bg=FRAME_BG)
        file_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        self.v_file_var = tk.StringVar()
        v_entry = ttk.Entry(file_frame, textvariable=self.v_file_var, width=45)
        v_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(file_frame, text="Browse", style="Secondary.TButton",
                   command=self._browse_verify_file).pack(side="left", padx=(10, 0))

        # Algorithm
        tk.Label(card, text="Algorithm", font=FONT_BOLD, bg=FRAME_BG, fg=TEXT_COLOR).grid(
            row=2, column=0, sticky="w", pady=(0, 2))
        algo_frame = tk.Frame(card, bg=FRAME_BG)
        algo_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        self.v_algo_var = tk.StringVar(value="sha256")
        v_algo_combo = ttk.Combobox(algo_frame, textvariable=self.v_algo_var,
                                    values=ALGORITHMS, state="readonly", font=FONT, width=20)
        v_algo_combo.pack(side="left")

        # Expected hash
        tk.Label(card, text="Expected checksum", font=FONT_BOLD, bg=FRAME_BG,
                 fg=TEXT_COLOR).grid(row=4, column=0, sticky="w", pady=(0, 2))
        hash_frame = tk.Frame(card, bg=FRAME_BG)
        hash_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        self.expected_var = tk.StringVar()
        exp_entry = ttk.Entry(hash_frame, textvariable=self.expected_var, width=50,
                              font=("Consolas", 9))
        exp_entry.pack(side="left", fill="x", expand=True)

        # Guess button
        guess_btn = ttk.Button(card, text="↻ Guess algorithm from hash",
                               style="Secondary.TButton", command=self._guess_algo)
        guess_btn.grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # Progress bar
        self.verify_progress = ttk.Progressbar(card, orient="horizontal",
                                               mode="determinate", length=300)
        self.verify_progress.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(5, 5))

        # Verify button
        self.verify_button = ttk.Button(card, text="Verify", style="Primary.TButton",
                                        command=self._start_verify)
        self.verify_button.grid(row=8, column=0, columnspan=2, pady=15)

        # Result label
        self.result_var = tk.StringVar()
        self.result_label = tk.Label(card, textvariable=self.result_var,
                                     font=("Segoe UI", 11, "bold"), bg=FRAME_BG,
                                     fg=SUCCESS_COLOR, wraplength=500, justify="left")
        self.result_label.grid(row=9, column=0, columnspan=2, sticky="w", pady=(5, 0))

    def _browse_verify_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.v_file_var.set(path)

    def _guess_algo(self):
        hash_str = self.expected_var.get().strip()
        if not hash_str:
            messagebox.showwarning("Empty", "Enter a hash string first.")
            return
        mapping = {
            32: "md5", 40: "sha1", 56: "sha224",
            64: "sha256", 96: "sha384", 128: "sha512"
        }
        algo = mapping.get(len(hash_str))
        if algo:
            self.v_algo_var.set(algo)
        else:
            messagebox.showinfo("Cannot guess", "Unable to guess algorithm from length.")

    def _start_verify(self):
        file_path = self.v_file_var.get().strip()
        expected = self.expected_var.get().strip()
        if not file_path or not expected:
            messagebox.showwarning("Missing Data", "File and expected hash are required.")
            return
        if not Path(file_path).exists():
            messagebox.showerror("Error", "File does not exist.")
            return

        self.verify_button.config(state="disabled")
        self.verify_progress["value"] = 0
        self.result_var.set("")

        self._running = True
        algo = self.v_algo_var.get()
        thread = threading.Thread(target=self._verify_worker,
                                  args=(Path(file_path), algo, expected), daemon=True)
        thread.start()
        self._poll_progress("verify")

    def _verify_worker(self, file_path, algo, expected):
        try:
            file_size = file_path.stat().st_size
            hash_func = hashlib.new(algo)
            bytes_read = 0
            with open(file_path, "rb") as f:
                while self._running:
                    chunk = f.read(BUFFER_SIZE)
                    if not chunk:
                        break
                    hash_func.update(chunk)
                    bytes_read += len(chunk)
                    percent = min(int(bytes_read / file_size * 100), 100) if file_size else 100
                    self._progress_queue.put(("progress", percent))
            digest = hash_func.hexdigest()
            if digest.lower() == expected.lower():
                self._progress_queue.put(("result", "✔ Match – the checksums are identical"))
            else:
                self._progress_queue.put(("result",
                    f"✘ Mismatch\nExpected: {expected}\nGot:      {digest}"))
        except Exception as e:
            self._progress_queue.put(("error", str(e)))
        finally:
            self._running = False

    # ---------- Common ----------
    def _poll_progress(self, mode):
        while not self._progress_queue.empty():
            msg = self._progress_queue.get_nowait()
            kind = msg[0]
            if kind == "progress":
                percent = msg[1]
                if mode == "generate":
                    self.gen_progress["value"] = percent
                else:
                    self.verify_progress["value"] = percent
            elif kind == "done":
                digest = msg[1]
                self.hash_var.set(digest)
                self.copy_button.config(state="normal")
                self.gen_button.config(state="normal")
                self.gen_progress["value"] = 100
            elif kind == "result":
                text = msg[1]
                self.result_var.set(text)
                if "Match" in text:
                    self.result_label.config(fg=SUCCESS_COLOR)
                else:
                    self.result_label.config(fg=FAIL_COLOR)
                self.verify_button.config(state="normal")
                self.verify_progress["value"] = 100
            elif kind == "error":
                messagebox.showerror("Error", msg[1])
                self.gen_button.config(state="normal")
                self.verify_button.config(state="normal")
                self.gen_progress["value"] = 0
                self.verify_progress["value"] = 0

        if self._running:
            self.root.after(100, self._poll_progress, mode)

    def _copy_hash(self):
        hash_val = self.hash_var.get()
        if hash_val:
            self.root.clipboard_clear()
            self.root.clipboard_append(hash_val)
            self.copy_button.config(text="Copied!")
            self.root.after(2000, lambda: self.copy_button.config(text="Copy"))


def main():
    root = tk.Tk()
    # Set a window icon (optional – create an .ico file or comment out)
    try:
        root.iconbitmap("icon.ico")  # replace with your icon file if you have one
    except:
        pass
    app = BeautifulChecksumApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()