import ast
import openai


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
        function_list, duplicates = [], []
        for fn in self.functions:
            class_name = fn.get('class_name', None)  # some code might not have a class
            function_list.append((fn['name'], get_function_ast_structure(fn['node']), class_name))

        for i in range(len(function_list)):
            for j in range(i + 1, len(function_list)):
                func1_name, struct1, class1 = function_list[i]
                func2_name, struct2, class2 = function_list[j]

                # Skipping comparison if both functions belong to different classes
                if class1 and class2 and class1 != class2:
                    continue

                similarity = jaccard_similarity(struct1, struct2)

                if similarity > self.SIMILARITY_THRESHOLD:
                    duplicates.append((func1_name, func2_name, round(similarity, 2)))
        return duplicates

    def semantic_duplicate_code_detector(self):
        pass


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


def refactor_code_w_openai(original_code, duplicates):
    API_KEY = "Use yours if you want to"

    prompt = gpt_prompt()

    for func1, func2, similarity in duplicates:
        prompt += f"Function {func1} and {func2} having (Jaccard Similarity: {similarity} which is not good)\n"

    prompt += "\n Original actual executable code: \n" + original_code

    client = openai.OpenAI(api_key=API_KEY)
    response = client.chat.completions.create(
        model='gpt-4-turbo',
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.1,
        max_tokens=1000,
    )
    raw_output = response.choices[0].message.content.strip()
    output = format_refactored_output(raw_output)
    return output


def gpt_prompt():
    return """You are given a Python code that contains structural duplicated functions.
    Your task is to refactor ONLY these duplicate functions while preserving the original functionality.
    Do not change any other parts of the code.
    Ensure that the refactored code maintains the exact same functionality as the original.
    Follow best practices in Python programming and avoid introducing new code smells.
    Return only the full refactored raw executable Python code, without any explanations, comments, extra formatting, or markdown syntax.
    The functions that require refactoring due to duplication are:
    """
def format_refactored_output(raw_output):
    if raw_output.startswith("```"):
        raw_output = raw_output.strip("```").strip()
        if raw_output.startswith("python"):
            raw_output = raw_output[len("python"):].strip()
    return raw_output
