class CodeSmellDetector:
    def __init__(self, functions):
        self.functions = functions

    MAX_LOC = 15
    MAX_PARAMS = 3

    def detectLongFunctions(self):
        pass

    def detectLongParameters(self):
        long_param_function = []
        for fn in self.functions:
            if len(fn['parameters']) > self.MAX_PARAMS:
                long_param_function.append(fn)
        return long_param_function

    def duplicateCodeDetector(self):
        pass

    def detectCodeSmells(self):
        return{
            'long_functions': self.detectLongFunctions(),
            'excess_parameters': self.detectLongParameters(),
            'duplicate_code': self.duplicateCodeDetector()
        }
