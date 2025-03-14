import ast
import os.path


class CodeParser:
    def __init__(self, file_path):
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"{file_path} not found")

        self.file_path = file_path
        self.tree = self.parse_input_code()

    def get_ASTree(self):
        return self.tree

    def parse_input_code(self):
        with open(self.file_path, 'r') as file:
            return ast.parse(file.read())


def parameter_extractor(node):

    # node.args.args has all the regular function arguments
    params = [i.arg for i in node.args.args]

    # node.args.vararg checks for variable arguments
    if node.args.vararg:
        params.append('*' + node.args.vararg.arg)  # .arg only gets the name so adding * in front
    if node.args.kwarg:
        params.append(('**' + node.args.kwarg.arg))

    return params


class FunctionExtractor:
    def __init__(self, as_tree, file_path):
        self.as_tree = as_tree
        self.file_path = file_path

    def function_details_extractor(self, node):
        return ({
            'name': node.name,
            'parameters': parameter_extractor(node),
            'loc': self.loc_calculator(node),
            'node': node    # storing ast node for duplicate code detection
        })

    def extract_functions(self):
        functions = []
        for node in ast.walk(self.as_tree):
            if isinstance(node, ast.FunctionDef):  # looks for function def
                functions.append(self.function_details_extractor(node))
        return functions

    def loc_calculator(self, node):
        with open(self.file_path, 'r') as f:
            lines = f.readlines()

        total_loc = lines[node.lineno - 1: node.end_lineno]

        final_loc = [
            line for line in total_loc
            if line.strip() and not line.strip().startswith("#") and not line.strip().startswith('"')
        ]

        return len(final_loc)
