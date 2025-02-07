import ast
import os.path


class CodeParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.tree = self.parseCode()

    def parseCode(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"{self.file_path} not found")
        with open(self.file_path, 'r') as file:
            return ast.parse(file.read())

    def getASTree(self):
        return self.tree


def parameterExtractor(node):
    """Returns a list of parameters"""

    # node.args.args has all the regular function arguments
    params = [i.arg for i in node.args.args]

    # node.args.vararg checks for variable arguments
    if node.args.vararg:
        params.append('*' + node.args.vararg.arg)  # .arg gets the name of it and adding * in front
    if node.args.kwarg:
        params.append(('**' + node.args.kwarg.arg))

    return params


class FunctionExtractor:
    def __init__(self, as_tree):
        self.as_tree = as_tree

    def functionDetailsExtractor(self, node):
        """Extracts details of the functions"""
        return({
            'name': node.name,
            'parameters': parameterExtractor(node),
            'loc': self.locCalculator(node)
        })

    def extractFunctions(self):
        functions = []
        for node in ast.walk(self.as_tree):
            if isinstance(node, ast.FunctionDef):       # looks for function def
                functions.append(self.functionDetailsExtractor(node))

        return functions

    def locCalculator(self, node):
        """Calculates the number of lines of code in a function."""
        pass
