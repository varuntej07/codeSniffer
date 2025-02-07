import ast


def functionExtractor(filePath):
    with open(filePath, 'r') as file:
        lines = file.read()

        tree = ast.parse(lines)
        functionNames = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functionName = node.name

                # node.args.args has all the regular function arguments
                params = [i.arg for i in node.args.args]

                # node.args.vararg checks for variable arguments
                if node.args.vararg:
                    params.append('*' + node.args.vararg.arg)  # .arg gets the name of it and adding * in front

                if node.args.kwarg:
                    params.append(('**' + node.args.kwarg.arg))

                functionNames.append((functionName, params))

        return functionNames


print(functionExtractor("C:/Users/varun/Desktop/Refactoring/input.txt"))
