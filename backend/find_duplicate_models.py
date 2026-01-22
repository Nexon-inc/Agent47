
import os
import re
from collections import defaultdict

def find_classes(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return re.findall(r'class\s+(\w+)\(Base\):', content)

agent_dir = r'c:\Users\John Kyalo\Desktop\REPOS\Agent47\backend\agents'
all_classes = defaultdict(list)

for agent in os.listdir(agent_dir):
    models_path = os.path.join(agent_dir, agent, 'app', 'models.py')
    if os.path.exists(models_path):
        classes = find_classes(models_path)
        for cls in classes:
            all_classes[cls].append(agent)

duplicates = {cls: agents for cls, agents in all_classes.items() if len(agents) > 1}

if duplicates:
    print("Found duplicate SQLAlchemy classes:")
    for cls, agents in duplicates.items():
        print(f"  - {cls}: {', '.join(agents)}")
else:
    print("No duplicate SQLAlchemy classes found (besides what's expected).")
