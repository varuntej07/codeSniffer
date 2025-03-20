This project is a Code Smell Detector and Refactoring Tool designed to analyze source code and detect common code smells. 
It also provides an option to refactor duplicated code automatically. The project includes a GUI for interaction.

Features

Detects Code Smells:
1. Long Method/Function: Flags methods/functions exceeding 15 lines.
2. Long Parameter List: Flags methods/functions with 4 or more parameters.
3. Duplicated Code: Uses Jaccard Similarity (threshold: 0.75) to detect duplicated code fragments.
4. Semantic Duplicated code: Detects if the code has semantic duplicates(two functions achieving same result but with different logic) if you click a button for that
   
Refactoring Capabilities:
Found duplicated code? No worries. This tool can refactor duplicate functions and generate a cleaner version so your code smells fresh again

If you're curious to check if ya code has bad smells, just clone the repo and run it on ya IDE and get rid of bad smells in ya code.

disclaimer - If you want to check for semantic duplication or refactor the structural duplicates, you'll need an OpenAI API key. 
Get API key and to set it up, just open the command prompt and enter: **setx OPENAI_API_KEY = your api-key**

If your code smells, don’t panic - just run it through this tool.
If your code still smells after using this… well, maybe the problem isn’t the code 😬
