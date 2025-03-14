import tkinter as tk
from tkinter import filedialog, messagebox
import detector
from extractor import CodeParser, FunctionExtractor


class CodeSmellGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Varun' Code Smell detector")
        self.root.geometry("600x800")

        self.upload_btn = tk.Button(root, text='Upload Python file', command=self.open_file)
        self.upload_btn.pack(pady=10)

        self.result_text = tk.Text(root, height=20, width=100)
        self.result_text.pack(pady=10)

    def open_file(self):
        file_path = filedialog.askopenfilename()  # filetypes=[("Python Files", "*.py")]

        if not file_path:
            return

        try:
            smells, duplicates = self.code_analyzer(file_path)
            self.result_text.delete(1.0, tk.END)  # clear previous results
            self.display_results(smells)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def code_analyzer(self, file_path):
        """Parses, extracts functions, detects code smells"""
        parser = CodeParser(file_path)

        # extracting the functions by taking parsed AST as an arg
        extractor = FunctionExtractor(parser.get_ASTree(), file_path)
        functions = extractor.extract_functions()

        # Initializing the code smell detector by passing extracted functions to detector
        detection = detector.CodeSmellDetector(functions)

        # smells hold each smell detection returns
        smells = detection.detect_code_smells()

        duplicates = detection.duplicate_code_detector()

        return smells, duplicates

    def display_results(self, smells):
        self.display_smells(smells['long_functions'], "Function {name} is too long with {loc} lines!\n")
        self.display_smells(smells['excess_parameters'], "Function {name} has {params} parameters, that's too much!\n")
        self.display_duplicate_code(smells['duplicate_code'])

    def display_smells(self, smell_exists, message):
        if smell_exists:
            for fn in smell_exists:
                self.result_text.insert(
                    tk.END,
                    message.format(name=fn['name'], loc=fn.get('loc', ''), params=len(fn['parameters']))
                )

    def display_duplicate_code(self, duplicates):
        if duplicates:
            for duplicate in duplicates:
                self.result_text.insert(
                    tk.END,
                    f"Functions '{duplicate[0]}' and '{duplicate[1]}' has duplicated code! with Jaccard Similarity of {duplicate[2]}\n"
                )
            self.refactor_btn = tk.Button(text='click to refactor', command=self.refactor_duplicate_code)
            self.refactor_btn.pack(pady=10)
        else:
            self.result_text.insert(tk.END, 'Nice! No Duplicate code found!!\n')

    def refactor_duplicate_code(self, ):
        pass
