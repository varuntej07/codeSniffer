import detector
from extractor import CodeParser, FunctionExtractor

if __name__ == '__main__':
    file_path = "C:/Users/varun/Desktop/Refactoring/input.txt"

    # 1. parses the input file and generates AST
    parser = CodeParser(file_path)

    # 2. extracting the functions by taking AST as an arg
    extractor = FunctionExtractor(parser.getASTree())
    functions = extractor.extractFunctions()

    # 3. Initializing the code smell detector by passing extracted functions to detector
    detection = detector.CodeSmellDetector(functions)

    # 4. results hold each smell detection returns
    results = detection.detectCodeSmells()

    if results['excess_parameters']:
        for fn in results['excess_parameters']:
            print(f"Function {fn['name']} has {len(fn['parameters'])} parameters, that's not good!!")
    else:
        print("Great!! No Long Parameters found!")
