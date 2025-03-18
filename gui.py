import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
import detector
from extractor import CodeParser, FunctionExtractor


class FileHandler:
    def read_file(self, file_path):
        try:
            with open(file_path, "r") as file:
                return file.read()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file: {str(e)}")
            return None


class Analyzer:
    def analyze(self, file_path):
        parser = CodeParser(file_path)
        extractor = FunctionExtractor(parser.get_ASTree(), file_path)
        functions = extractor.extract_functions()
        detection = detector.CodeSmellDetector(functions)
        smells = detection.detect_code_smells()
        duplicates = detection.duplicate_code_detector()
        return smells, duplicates


class CodeSmellGUI:
    """A GUI application for detecting and refactoring code smells in Python files."""

    FILE_TYPES = [("Python Files", "*.py")]
    SMELL_CONFIGS = [
        ("Long functions", "long_functions", lambda fn: f"  - {fn['name']} with {fn['loc']} lines\n"),
        ("Excess parameters", "excess_parameters",
         lambda fn: f"  - {fn['name']} with {len(fn['parameters'])} parameters\n"),
        ("Structural duplicates", "duplicates", lambda d: f"  - {d[0]} and {d[1]} (Similarity: {d[2]})\n")
    ]

    def __init__(self, root):
        self.root = root
        self.root.title("Varun's Code Smell Detector")
        self.root.geometry("800x500")
        self.root.configure(bg="#000000")

        self.title_label = ttk.Label(root, text="Code Smell Detector", font=("Consolas", 16, "bold"),
                                     foreground="#00ff00", background="#1e1e1e")
        self.title_label.grid(row=0, column=0, columnspan=3, pady=10)

        self.upload_btn = ttk.Button(root, text='Upload Python File', command=self.open_file)
        self.upload_btn.grid(row=1, column=0, columnspan=3, padx=10, pady=10)

        self.result_text = ScrolledText(root, height=20, width=80, wrap=tk.WORD, font=("Consolas", 10, "bold"),
                                        bg="#000000", fg="#ffffff", insertbackground="#ffffff")
        self.result_text.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        self.result_text.tag_configure("header", foreground="red")
        self.result_text.tag_configure("success", foreground="green")
        self.result_text.tag_configure("highlight", foreground="yellow")
        self.result_text.tag_configure("info", foreground="white")

        self.button_frame = ttk.Frame(root)
        self.button_frame.grid(row=3, column=0, columnspan=3, sticky="ew")

        self._configure_styles()

        self.semantic_check_btn = ttk.Button(self.button_frame, text='Check Semantic Duplicates',
                                             command=self.check_semantic_duplicates, state=tk.DISABLED, style="TButton")
        self.semantic_check_btn.pack(side="left", padx=10, pady=10)

        self.refactor_btn = ttk.Button(self.button_frame, text='Refactor Duplicates',
                                       command=self.refactor_duplicate_code, state=tk.DISABLED, style="TButton")
        self.refactor_btn.pack(side="right", padx=10, pady=10)

        self.file_handler = FileHandler()
        self.analyzer = Analyzer()

        root.grid_rowconfigure(2, weight=1)
        root.grid_rowconfigure(3, weight=0)
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)
        root.grid_columnconfigure(2, weight=1)

        self.file_path = None
        self.original_code = None
        self.duplicates = None

    def _configure_styles(self):
        """Configures the styling for UI elements using a style map."""
        style = ttk.Style()
        style_map = {
            "TButton": {"background": "#000000", "font": ("Consolas", 10, "bold"), "padding": 6},
            "TLabel": {"foreground": "#00ff00", "background": "#1e1e1e", "font": ("Consolas", 12, "bold")}
        }
        for style_name, config in style_map.items():
            style.configure(style_name, **config)

    def open_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=self.FILE_TYPES)
        if not self.file_path:
            return
        self.original_code = self.file_handler.read_file(self.file_path)
        self.code_analyzer()

    def code_analyzer(self):
        """Parses, extracts functions, detects code smells."""
        smells, self.duplicates = self.analyzer.analyze(self.file_path)
        self.result_text.delete(1.0, tk.END)
        self.display_results(smells, self.duplicates)
        self.semantic_check_btn.config(state=tk.NORMAL)
        self.refactor_btn.config(state=tk.NORMAL if self.duplicates else tk.DISABLED)

    def display_results(self, smells, duplicates):
        smell_data = {
            'long_functions': smells['long_functions'],
            'excess_parameters': smells['excess_parameters'],
            'duplicates': duplicates
        }
        if not self._has_smells(smell_data):
            self.result_text.insert(tk.END, "No code smells found.\n", "success")
        else:
            self._display_smell_header(smell_data)
            for name, key, format_func in self.SMELL_CONFIGS:
                if smell_data[key]:
                    self._display_smell_type(name, smell_data[key], format_func)
        self.result_text.insert(tk.END, "\nYou can check for semantic duplicates if you want to...\n", "info")

    def _has_smells(self, smell_data):
        return any(bool(smell_data[key]) for _, key, _ in self.SMELL_CONFIGS)

    def _display_smell_header(self, smell_data):
        present_smells = [name for name, key, _ in self.SMELL_CONFIGS if smell_data[key]]
        self.result_text.insert(tk.END, f"Code smells detected: {', '.join(present_smells)}\n", "header")

    def _display_smell_type(self, smell_name, smell_list, format_func):
        self.result_text.insert(tk.END, f"- {smell_name}: {len(smell_list)}\n", "highlight")
        for item in smell_list:
            self.result_text.insert(tk.END, format_func(item))

    def _run_openai_operation(self, operation):
        """Runs an OpenAI operation with error handling to catch and display errors."""
        try:
            openai_client = detector.OpenAIClient()
            return operation(openai_client)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return None

    def check_semantic_duplicates(self):
        result = self._run_openai_operation(
            lambda client: client.detect_semantic_duplicates(self.original_code)
        )
        if result:
            self.result_text.insert(tk.END, "\n=== Semantic Duplicates Found ===\n", "header")
            for func1, func2 in result:
                self.result_text.insert(tk.END, f"- {func1} and {func2}\n", "highlight")
        elif result is not None:
            self.result_text.insert(tk.END, "\nNo semantic duplicates found.\n", "success")

    def refactor_duplicate_code(self):
        result = self._run_openai_operation(
            lambda client: client.refactor_code(self.original_code, self.duplicates)
        )
        if result:
            save_refactored_code(result)


def save_refactored_code(refactored_code):
    """Saves refactored code to a user-specified file."""
    save_file = filedialog.asksaveasfilename(
        defaultextension='.py',
        filetypes=[('Python files', '*.py')],
        initialfile='refactored_code'
    )
    if save_file:
        with open(save_file, 'w') as file:
            file.write(refactored_code)
        messagebox.showinfo("Success", f"Refactored code saved at: {save_file}")
