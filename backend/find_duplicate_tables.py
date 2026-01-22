
import os
import re
from collections import defaultdict

def find_table_names(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return re.findall(r'__tablename__\s*=\s*"([^"]+)"', content)

agent_dir = r'c:\Users\John Kyalo\Desktop\REPOS\Agent47\backend\agents'
all_tables = defaultdict(list)

for agent in os.listdir(agent_dir):
    models_path = os.path.join(agent_dir, agent, 'app', 'models.py')
    if os.path.exists(models_path):
        tables = find_table_names(models_path)
        for table in tables:
            all_tables[table].append(agent)

duplicates = {table: agents for table, agents in all_tables.items() if len(agents) > 1}

if duplicates:
    print("Found duplicate Table names:")
    for table, agents in duplicates.items():
        print(f"  - {table}: {', '.join(agents)}")
else:
    print("No duplicate Table names found.")
