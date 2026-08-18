import json

with open('cleanup_report.json', 'r') as f:
    data = json.load(f)

confirmed = [d for d in data if d['category'] == 'CONFIRMED UNUSED']
likely = [d for d in data if d['category'] == 'LIKELY UNUSED']
keep = [d for d in data if d['category'] == 'KEEP']

with open('C:\\Users\\Naveen\\.gemini\\antigravity-ide\\brain\\b57ff017-a2bd-41ce-bacf-70f72877f456\\cleanup_report.md', 'w') as f:
    f.write('# Cleanup Report\n\n')
    
    f.write('## CONFIRMED UNUSED\n\n')
    f.write('These files appear to have no references anywhere in the codebase and are safe to delete.\n\n')
    f.write('| Path | Size (Bytes) | Last Modified | Reason |\n')
    f.write('|---|---|---|---|\n')
    for d in confirmed:
        f.write(f'| `{d["path"]}` | {d["size"]} | {d["mtime"]} | {d["reason"]} |\n')
        
    f.write('\n## LIKELY UNUSED (Review Required)\n\n')
    f.write('These files have no direct code references but might be used dynamically (e.g., uploads, generated exports, or dynamic data).\n\n')
    f.write('| Path | Size (Bytes) | Last Modified | Reason |\n')
    f.write('|---|---|---|---|\n')
    for d in likely:
        f.write(f'| `{d["path"]}` | {d["size"]} | {d["mtime"]} | {d["reason"]} |\n')

    f.write('\n## KEEP\n\n')
    f.write('These files are entry points, configuration files, or are actively referenced in the code.\n\n')
    f.write('| Path | Size (Bytes) | Last Modified | Reason |\n')
    f.write('|---|---|---|---|\n')
    for d in keep:
        f.write(f'| `{d["path"]}` | {d["size"]} | {d["mtime"]} | {d["reason"]} |\n')
