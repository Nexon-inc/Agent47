
import os
import re
from collections import defaultdict

def find_classes(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return re.findall(r'class\s+(\w+)\(Base\):', content)

jackie_models = r'c:\Users\John Kyalo\Desktop\REPOS\Agent47\backend\agents\jackie\app\models.py'
classes = find_classes(jackie_models)
counts = defaultdict(int)
for cls in classes:
    counts[cls] += 1

internal_duplicates = {cls: count for cls, count in counts.items() if count > 1}
if internal_duplicates:
    print("Internal duplicates in Jackie's models.py:")
    for cls, count in internal_duplicates.items():
        print(f"  - {cls}: {count} times")
else:
    print("No internal duplicates in Jackie's models.py.")
