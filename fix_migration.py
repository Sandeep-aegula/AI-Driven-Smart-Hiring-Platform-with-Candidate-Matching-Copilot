import re

with open('backend/database/migrate_json_to_mysql.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove benefits field from Job creation
content = content.replace('benefits=job_json.get("benefits", []),\n            ', '')
content = content.replace('benefits=job_json.get("benefits", []),', '')

with open('backend/database/migrate_json_to_mysql.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed benefits field')
