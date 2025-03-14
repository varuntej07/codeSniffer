import ast


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
            'duplicate_code': self.duplicate_code_detector()
        }

    def detect_threshold_exceeding(self, key, threshold):
        return [fn for fn in self.functions if (len(fn[key]) if isinstance(fn[key], list) else fn[key]) > threshold]

    def duplicate_code_detector(self):
        function_structures = {fn['name']: get_function_ast_structure(fn['node']) for fn in self.functions}

        duplicates = []
        function_list = list(function_structures.items())

        for i in range(len(function_list)):
            for j in range(i + 1, len(function_list)):
                func1_name, struct1 = function_list[i]
                func2_name, struct2 = function_list[j]

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
