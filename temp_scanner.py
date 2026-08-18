import os
import re
import json
from pathlib import Path
from datetime import datetime

TARGET_DIR = r"C:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot"
SKIP_DIRS = {'.git', '.venv', '__pycache__', '.pytest_cache', 'node_modules', '.streamlit', '.claude'}
CONFIG_FILES = {'.env', '.gitignore', 'requirements.txt', 'readme.md', 'license', 'pyproject.toml', 'dockerfile', 'docker-compose.yml', 'config.json'}
ENTRY_POINTS = {'app.py', 'app1.py', 'main.py', 'manage.py', 'setup.py'}
SENSITIVE_FILES = {'.env', 'ai_recruitment_copilot.db', 'storage.json'}

def scan_files():
    all_files = []
    text_files = []
    for root, dirs, files in os.walk(TARGET_DIR):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, TARGET_DIR)
            size = os.path.getsize(full_path)
            mtime = os.path.getmtime(full_path)
            
            is_text = False
            if file.endswith(('.py', '.md', '.txt', '.html', '.css', '.js', '.json', '.yml', '.yaml', '.sh', '.bat', '.env')):
                is_text = True
                text_files.append((full_path, rel_path))
                
            all_files.append({
                'path': full_path,
                'rel_path': rel_path,
                'name': file,
                'name_no_ext': os.path.splitext(file)[0],
                'size': size,
                'mtime': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'is_text': is_text
            })
    return all_files, text_files

def analyze():
    all_files, text_files = scan_files()
    
    # Pre-read all text file contents for faster searching
    file_contents = {}
    for fp, rp in text_files:
        try:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                file_contents[rp] = f.read()
        except:
            pass

    results = []
    
    for f in all_files:
        name = f['name'].lower()
        rel_path_f = f['rel_path'].replace('\\', '/')
        module_path = rel_path_f.replace('.py', '').replace('/', '.')
        
        category = "CONFIRMED UNUSED"
        reason = ""
        is_sensitive = name in SENSITIVE_FILES or name.endswith('.db')
        
        # Check if config or entry point
        if name in CONFIG_FILES:
            category = "KEEP"
            reason = "Config/Meta file"
        elif name in ENTRY_POINTS:
            category = "KEEP"
            reason = "Entry point"
        else:
            # Check references
            referenced = False
            for src_rp, content in file_contents.items():
                if src_rp == f['rel_path']:
                    continue
                
                # Check for filename or module name
                if f['name'] in content:
                    referenced = True
                    break
                if f['name'].endswith('.py') and (f['name_no_ext'] in content or module_path in content):
                    referenced = True
                    break
            
            if referenced:
                category = "KEEP"
                reason = "Actively referenced in code"
            else:
                # If no reference, maybe it's in uploads or is a data file
                if 'uploads' in rel_path_f or 'data' in rel_path_f or not f['is_text']:
                    category = "LIKELY UNUSED"
                    reason = "No references found, but it's a data/upload file (might be dynamic)"
                elif f['name'].endswith(('.pyc', '.log', '.bak')):
                    category = "CONFIRMED UNUSED"
                    reason = "Log/Cache/Backup file"
                else:
                    category = "CONFIRMED UNUSED"
                    reason = "No references found anywhere"
                    
        if is_sensitive:
            reason += " (FLAG: SENSITIVE DATA)"
            
        results.append({
            'path': f['rel_path'],
            'category': category,
            'reason': reason,
            'size': f['size'],
            'mtime': f['mtime']
        })

    with open(os.path.join(TARGET_DIR, 'cleanup_report.json'), 'w') as out:
        json.dump(results, out, indent=2)

if __name__ == "__main__":
    analyze()
