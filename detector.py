import ast
import openai
import json
import os


class ASTAnalyzer:
    """Handles AST-based analysis for function structure and operations."""
    @staticmethod
    def get_function_ast_structure(node):
        """Extracts a set representing the AST structure while ignoring trivial elements."""
        ignore_nodes = {ast.Load, ast.Store, ast.Expr, ast.arguments, ast.arg, ast.Attribute}
        structure = set()

        for n in ast.walk(node):
            if type(n) in ignore_nodes:
                continue

            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                structure.add(f"CALL_{n.func.id}")  # Normalize function calls
            else:
                structure.add(type(n).__name__)
        return structure

    @staticmethod
    def count_ast_nodes(node):
        """Counts the number of AST nodes in a function, excluding trivial ones."""
        ignore_nodes = (ast.Load, ast.Store, ast.arguments, ast.arg)
        return sum(1 for n in ast.walk(node) if not isinstance(n, ignore_nodes))

    @staticmethod
    def extract_unique_operations(ast_node):
        """Gathers unique operations (e.g: BinOp, Compare) from a function AST."""
        ops = set()
        for node in ast.walk(ast_node):
            if isinstance(node, (ast.BinOp, ast.UnaryOp, ast.Compare)):
                ops.add(type(node).__name__)
        return ops

    @staticmethod
    def compute_unique_operation_penalty(ast1, ast2):
        """Penalizes similarity if the two functions perform different unique operations."""

        unique_ops1 = ASTAnalyzer.extract_unique_operations(ast1)
        unique_ops2 = ASTAnalyzer.extract_unique_operations(ast2)

        uncommon_ops = unique_ops1.symmetric_difference(unique_ops2)
        penalty = len(uncommon_ops) * 0.05
        return min(penalty, 0.5)  # Cap the penalty at 0.5


def jaccard_similarity(set1, set2):
    """Calculates Jaccard Similarity between two sets representing AST structures."""

    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union else 0


def is_wrapper_function(ast_node):
    """Identifies if a function is a wrapper (e.g. Adapter Pattern).
    We assume it's a wrapper if it has exactly one function call and no other logic."""

    calls = [node for node in ast.walk(ast_node) if isinstance(node, ast.Call)]
    if len(calls) == 1:
        call_node = calls[0]
        return isinstance(call_node.func, ast.Name)
    return False


class CodeSmellDetector:
    """Detects code smells:
    - Long functions (over MAX_LOC lines)
    - Excessive function parameters (over MAX_PARAMS)
    - Duplicate code (using AST-based Jaccard similarity)"""

    def __init__(self, functions, MAX_LOC=15, MAX_PARAMS=3, SIMILARITY_THRESHOLD=0.75, min_complexity_threshold=10):
        self.functions = functions
        self.MAX_LOC = MAX_LOC
        self.MAX_PARAMS = MAX_PARAMS
        self.SIMILARITY_THRESHOLD = SIMILARITY_THRESHOLD
        self.MIN_COMPLEXITY_THRESHOLD = min_complexity_threshold  # Minimum AST nodes to consider a function non-trivial

    def detect_code_smells(self):
        """Returns a dictionary containing: 'long_functions' and 'excess_parameters'"""
        return {
            'long_functions': self._detect_threshold_exceeding('loc', self.MAX_LOC),
            'excess_parameters': self._detect_threshold_exceeding('parameters', self.MAX_PARAMS),
        }

    def _detect_threshold_exceeding(self, key, threshold):
        """Generic helper that checks if a function's attribute (like LOC or param count) exceeds a threshold."""
        return [
            fn for fn in self.functions
            if (len(fn[key]) if isinstance(fn[key], list) else fn[key]) > threshold
        ]   # loc could be an int, while parameters could be a list.

    def duplicate_code_detector(self):
        """Detects structurally duplicate functions using Jaccard similarity, ignoring trivial wrappers
        and penalizing unique operations."""
        function_structures = self._get_function_structures()
        duplicates = []

        for i in range(len(function_structures)):
            for j in range(i + 1, len(function_structures)):
                func1_data, func2_data = function_structures[i], function_structures[j]

                # If both belong to different classes, skip as we only compare functions within the same class.
                if func1_data[2] and func2_data[2] and (func1_data[2] != func2_data[2]):
                    continue

                similarity = self._compute_function_similarity(func1_data, func2_data)
                if similarity > self.SIMILARITY_THRESHOLD:
                    duplicates.append((func1_data[0], func2_data[0], round(similarity, 2)))
        return duplicates

    def _get_function_structures(self):
        """Gathers (function_name, set_of_ast_structures, class_name, ast_node) for each function
        that exceeds the min complexity threshold."""
        func_structs = []
        for fn in self.functions:
            node = fn.get('node')
            if not node:
                continue

            # Only include non-trivial functions
            if ASTAnalyzer.count_ast_nodes(node) > self.MIN_COMPLEXITY_THRESHOLD:
                class_name = fn.get('class_name', None)
                ast_structure = ASTAnalyzer.get_function_ast_structure(node)
                func_structs.append((fn['name'], ast_structure, class_name, node))
        return func_structs

    def _compute_function_similarity(self, func1_data, func2_data):
        """Computes the similarity of two functions by combining Jaccard and an operation-based penalty.
        Ignores wrappers entirely by returning similarity=0 if both are wrappers."""

        (_, struct1, _, ast1) = func1_data
        (_, struct2, _, ast2) = func2_data

        # If both are simple wrappers, consider them not duplicates
        if is_wrapper_function(ast1) and is_wrapper_function(ast2):
            return 0

        similarity = jaccard_similarity(struct1, struct2)

        # Penalty for unique operations
        penalty = ASTAnalyzer.compute_unique_operation_penalty(ast1, ast2)
        return max(similarity - penalty, 0)


class OpenAIClient:
    """Refactors duplicated code using OpenAI GPT, optionally detecting semantic duplicates."""
    API_KEY = os.getenv('OPENAI_API_KEY')

    def __init__(self):
        try:
            self.client = openai.OpenAI(api_key=self.API_KEY)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenAI client: {str(e)}")

    def get_gpt_response(self, prompt):
        """Sends a prompt to GPT and returns the response."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Unexpected Error: {str(e)}"

    def gpt_prompt(self):
        return """You are given a Python code snippet and a list of structural duplicate function pairs. 
        Your task is to refactor only these duplicate functions to eliminate duplication while preserving the original functionality. 
        In particular, for pairs of functions that return the same type of value, aim to create a single function that can serve both purposes by accepting an additional parameter to control the specific behavior, and adjust the original functions to utilize this new function. 
        Ensure that the refactored code works exactly as the original and follows best practices in Python programming, avoiding new code smells. 
        Return only the full refactored Python code without any explanations, comments, or extra formatting.
        The duplicate function pairs are:
        """

    def refactor_code(self, original_code, duplicates):
        """Sends structurally duplicated functions to GPT for refactoring."""
        prompt = self.gpt_prompt()

        for func1, func2, similarity in duplicates:
            prompt += f"Function '{func1}' and '{func2}' having Jaccard Similarity: {similarity}\\n"

        prompt += "\\n Original actual executable code: \\n" + original_code
        response = self.get_gpt_response(prompt)
        return format_refactored_output(response)

    def detect_semantic_duplicates(self, original_code):
        """Detects semantic duplicates by analyzing the full code with GPT."""

        prompt = f"""You are an expert software refactoring assistant. Analyze the given Python code and find 
        functions that are **semantically the same** but implemented differently.
        Provide the output as JSON with key 'semantic_duplicates': [(function1, function2), ...].
        If none, return {{\"semantic_duplicates\": []}}.
        Here is the code:\n\n:{original_code}"""

        try:
            response = self.get_gpt_response(prompt)
            result = json.loads(response)
            return result.get("semantic_duplicates", [])
        except json.JSONDecodeError:
            return []

def format_refactored_output(raw_output):
    """Cleans GPT responses to remove backticks and Python markers."""
    if raw_output.startswith("```"):
        raw_output = raw_output.strip("```").strip()
        if raw_output.startswith("python"):
            raw_output = raw_output[len("python"):].strip()
    return raw_output
