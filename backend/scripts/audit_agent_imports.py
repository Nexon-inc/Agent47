import os
import ast
import glob
import sys

AGENTS_DIR = r"C:\Users\John Kyalo\Desktop\REPOS\Agent47\backend\agents"

def get_defined_models(agent_name):
    models_file = os.path.join(AGENTS_DIR, agent_name, "app", "models.py")
    if not os.path.exists(models_file):
        return set()
    
    with open(models_file, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read())
        except Exception as e:
            print(f"Error parsing {models_file}: {e}")
            return set()
            
    models = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            models.add(node.name)
    return models

def check_imports(agent_name, defined_models):
    agent_path = os.path.join(AGENTS_DIR, agent_name)
    mismatches = []
    
    for root, _, files in os.walk(agent_path):
        for file in files:
            if not file.endswith(".py") or file == "models.py":
                continue
                
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    tree = ast.parse(content)
            except Exception as e:
                # print(f"Error parsing {file_path}: {e}")
                continue
                
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    # Check for "from ..models import ..." or "from .models import ..."
                    # Note: level 1 = ., level 2 = ..
                    if node.module in [None, 'models'] or (node.module and 'models' in node.module):
                        # This is a bit heuristic. We care if they are importing FROM models.
                        # Using string matching for the import line might be easier but AST is robust for multiline.
                        pass

    # Regex fallback for imports because separate AST analysis for 'From' nodes with relative imports is tricky without context
    # Let's just scan lines for simplicity and robustness
    
    import re
    # Match: from ..models import X, Y, Z
    # Match: from .models import X
    import_pattern = re.compile(r"from \.*models import ([\w\s,]+)")
    
    for root, _, files in os.walk(agent_path):
        for file in files:
            if not file.endswith(".py") or file == "models.py":
                continue
                
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines):
                match = import_pattern.search(line)
                if match:
                    # This only captures single line imports, logic needs to be robust for multiline parens
                    # But typical issues here are simple lines.
                    # Parse the imported names
                    imported_block = match.group(1)
                    # Handle ( ) multiline
                    if "(" in imported_block and ")" not in imported_block:
                         # Read ahead
                         idx = i + 1
                         while idx < len(lines):
                             imported_block += lines[idx]
                             if ")" in lines[idx]:
                                 break
                             idx += 1
                    
                    # Clean up
                    imported_block = imported_block.replace("(", "").replace(")", "").replace("\n", " ")
                    imports = [x.strip().split(" as ")[0].strip() for x in imported_block.split(",")]
                    
                    for imp in imports:
                        if not imp: continue
                        if imp not in defined_models:
                            # It might be in core/models? But here we check if they expect it in local models.
                            # If it is NOT in defined_models, it's a potential mismatch OR it's a re-export we missed.
                            # But we assume models.py defines models.
                            mismatches.append({
                                "file": file,
                                "import": imp,
                                "agent": agent_name
                            })

    return mismatches

def main():
    agents = [d for d in os.listdir(AGENTS_DIR) if os.path.isdir(os.path.join(AGENTS_DIR, d))]
    
    all_mismatches = {}
    
    for agent in agents:
        print(f"Analyzing Agent: {agent}...")
        models = get_defined_models(agent)
        # print(f"  Defined models: {models}")
        
        mismatches = check_imports(agent, models)
        if mismatches:
            all_mismatches[agent] = mismatches
            
    print("\n--- ANALYSIS RESULTS ---")
    for agent, issues in all_mismatches.items():
        print(f"\nAgent: {agent}")
        for issue in issues:
            print(f"  File: {issue['file']} imports '{issue['import']}' which is NOT in {agent}/app/models.py")

if __name__ == "__main__":
    main()
