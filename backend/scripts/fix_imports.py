
import os
import sys

def replace_in_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'from ' in content or 'import ' in content:
            new_content = content.replace('from ', 'from ').replace('import ', 'import ')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {file_path}")

    except Exception as e:
        print(f"Error processing file {file_path}: {e}", file=sys.stderr)

def main():
    # Run from the root of the project
    backend_dir = 'backend'
    if not os.path.isdir(backend_dir):
        print(f"Error: Directory '{backend_dir}' not found.", file=sys.stderr)
        sys.exit(1)

    for root, _, files in os.walk(backend_dir):
        for file in files:
            if file.endswith('.py'):
                replace_in_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
