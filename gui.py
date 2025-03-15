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

        self.refactor_btn = None
        self.file_path = None
        self.original_code = None
        self.semantic_check_btn = None

    def open_file(self):
        self.file_path = filedialog.askopenfilename()  # filetypes=[("Python Files", "*.py")]

        if not self.file_path:
            return

        self.original_code = self.read_file()

        self.reset_buttons()

        try:
            smells, duplicates = self.code_analyzer()
            self.result_text.delete(1.0, tk.END)  # clear previous results
            self.display_results(smells, duplicates)
            self.semantic_check_btn = tk.Button(self.root, text='check semantic duplicates', command=self.check_semantic_duplicates)
            self.semantic_check_btn.pack(pady=10)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def reset_buttons(self):
        for btn in [self.refactor_btn, self.semantic_check_btn]:
            if btn:
                btn.destroy()
        self.refactor_btn, self.semantic_check_btn = None, None

    def read_file(self):
        with open(self.file_path, "r") as file:
            return file.read()

    def code_analyzer(self):
        """Parses, extracts functions, detects code smells"""
        parser = CodeParser(self.file_path)

        # extracting the functions by taking parsed AST as an arg
        extractor = FunctionExtractor(parser.get_ASTree(), self.file_path)
        functions = extractor.extract_functions()

        # Initializing the code smell detector by passing extracted functions to detector
        detection = detector.CodeSmellDetector(functions)

        # smells hold two smell detection returns
        smells = detection.detect_code_smells()

        duplicates = detection.duplicate_code_detector()

        return smells, duplicates

    def display_results(self, smells, duplicates):
        self.display_smells(smells['long_functions'], "Function {name} is too long with {loc} lines!\n")
        self.display_smells(smells['excess_parameters'], "Function {name} has {params} parameters, that's too much!\n")
        self.display_duplicate_code(duplicates)

    def display_smells(self, smell_exists, message):
        if smell_exists:
            for fn in smell_exists:
                self.result_text.insert(
                    tk.END,
                    message.format(name=fn['name'], loc=fn.get('loc', ''), params=len(fn['parameters']))
                )

    def display_duplicate_code(self, duplicates):
        if duplicates:
            self.result_text.insert(tk.END, "\n Structural Duplicates Found:\n")
            for duplicate in duplicates:
                self.result_text.insert(
                    tk.END,
                    f"Functions '{duplicate[0]}' and '{duplicate[1]}' has similar structure! (Jaccard Similarity: {duplicate[2]})\n"
                )
            self.refactor_btn = tk.Button(self.root, text='click to refactor',
                                          command=lambda: refactor_duplicate_code(duplicates, self.original_code))
            self.refactor_btn.pack(pady=10)
        else:
            self.result_text.insert(tk.END, 'Great! No Duplicate code found!!\n')

    def check_semantic_duplicates(self):
        if not self.original_code:
            messagebox.showerror("Error!", "Please upload a file first!!")
            return

        try:
            openai_client = detector.OpenAIClient()
            semantic_duplicates = openai_client.detect_semantic_duplicates(self.original_code)

            self.result_text.insert(tk.END, "\nSemantic Duplicates Found:\n" if semantic_duplicates else "\nYour code has no Semantic Duplicate functions!\n")
            for func1, func2 in semantic_duplicates:
                self.result_text.insert(tk.END, f"Functions '{func1}' and '{func2}' are performing same thing and are semantically similar!\n")
        except Exception as e:
            messagebox.showerror("Error", str(e))

def refactor_duplicate_code(duplicates, original_code):
    try:
        openai_client = detector.OpenAIClient()
        refactored_code = openai_client.refactor_code(original_code, duplicates)
    except ValueError as e:
        messagebox.showerror("Error", str(e))
        return

    save_refactored_code(refactored_code)


def save_refactored_code(refactored_code):
    save_file = filedialog.asksaveasfilename(
        defaultextension='.py',
        filetypes=[('Python files', '*py')],
        initialfile='refactored_code'
    )
    if save_file:
        with open(save_file, 'w') as file:
            file.write(refactored_code)
        tk.messagebox.showinfo("Success", f"Refactored code saved at: \n {save_file}")
