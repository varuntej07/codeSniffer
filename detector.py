import ast
import openai
import json
import os


class CodeSmellDetector:
    def __init__(self, functions):
        self.functions = functions

    MAX_LOC = 15
    MAX_PARAMS = 3
    SIMILARITY_THRESHOLD = 0.75

    def detect_code_smells(self):
        return {
            'long_functions': self.detect_threshold_exceeding('loc', self.MAX_LOC),
            'excess_parameters': self.detect_threshold_exceeding('parameters', self.MAX_PARAMS),
        }

    def detect_threshold_exceeding(self, key, threshold):
        return [fn for fn in self.functions if (len(fn[key]) if isinstance(fn[key], list) else fn[key]) > threshold]

    def duplicate_code_detector(self):
        function_structures, duplicates = [], []
        for fn in self.functions:
            class_name = fn.get('class_name', None)
            function_structures.append((fn['name'], get_function_ast_structure(fn['node']), class_name))

        for i in range(len(function_structures)):
            for j in range(i + 1, len(function_structures)):
                func1_name, struct1, class1 = function_structures[i]
                func2_name, struct2, class2 = function_structures[j]

                if class1 and class2 and class1 != class2:
                    continue

                similarity = jaccard_similarity(struct1, struct2)
                if similarity > self.SIMILARITY_THRESHOLD:
                    duplicates.append((func1_name, func2_name, round(similarity, 2)))

        return duplicates


def jaccard_similarity(set1, set2):
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union != 0 else 0


def get_function_ast_structure(node):
    ignore_nodes = (ast.Load, ast.Store, ast.Expr, ast.arguments, ast.arg, ast.Attribute)
    structure = set()

    for n in ast.walk(node):
        if isinstance(n, ignore_nodes):
            continue

        node_type = type(n).__name__

        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            structure.add(f"CALL_{n.func.id}")  # Normalize function calls
        else:
            structure.add(node_type)  # Generic structure-based representation

    return structure


def format_refactored_output(raw_output):
    if raw_output.startswith("```"):
        raw_output = raw_output.strip("```").strip()
        if raw_output.startswith("python"):
            raw_output = raw_output[len("python"):].strip()
    return raw_output


class OpenAIClient:
    API_KEY = os.getenv('OPENAI_API_KEY')

    def __init__(self):
        self.client = openai.OpenAI(api_key=self.API_KEY)

    def get_gpt_response(self, prompt):
        """Sends a prompt to GPT and returns the response."""
        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        return response.choices[0].message.content.strip()

    def gpt_prompt(self):
        return """You are given a Python code that contains structural duplicated functions.
        Your task is to refactor ONLY these duplicate functions while preserving the original functionality.
        Do not change any other parts of the code.
        Ensure that the refactored code maintains the exact same functionality as the original.
        Follow best practices in Python programming and avoid introducing new code smells.
        Return only the full refactored raw executable Python code, without any explanations, comments, extra formatting, or markdown syntax.
        The functions that require refactoring due to duplication are:
        """

    def refactor_code(self, original_code, duplicates):
        """Sends structurally duplicated functions to GPT for refactoring."""
        prompt = self.gpt_prompt()

        for func1, func2, similarity in duplicates:
            prompt += f"Function {func1} and {func2} having (Jaccard Similarity: {similarity} which is not good)\n"

        prompt += "\n Original actual executable code: \n" + original_code

        response = self.get_gpt_response(prompt)
        return format_refactored_output(response)

    def detect_semantic_duplicates(self, original_code):
        """Detects semantic duplicates by analyzing the full code with GPT."""
        prompt = f"""You are an expert software refactoring assistant. Analyze the given Python code and find functions that are **semantically the same** but implemented differently.
        - Two functions are considered semantically duplicate if they **achieve the same result** using different logic.
        - Ignore syntax differences like slicing vs loops, recursion vs iteration, or different variable names.
        - Provide the output as a JSON object with the key "semantic_duplicates" containing a list of function pairs: {{"semantic_duplicates": [(function1, function2), ...]}}.
        - If there are no semantic duplicates, return an empty list like this: {{"semantic_duplicates": []}}
        Here is the code to analyze\n\n:{original_code}"""

        try:
            response = self.get_gpt_response(prompt)
            result = json.loads(response)
            return result.get("semantic_duplicates", [])
        except json.JSONDecodeError:
            return []
