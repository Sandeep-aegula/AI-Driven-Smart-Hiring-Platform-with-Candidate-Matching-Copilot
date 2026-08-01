with open('backend/database/migrate_json_to_mysql.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the broken employee email lookup
old = """    if email:
        stmt = select(Candidate).where(Candidate.email == email).limit(1)
        emp = Employee("""

new = """    if email:
        stmt = select(Candidate).where(Candidate.email == email).limit(1)
        res = await session.execute(stmt)
        cand = res.scalar_one_or_none()
        if cand:
            cand_id = cand.id
    emp = Employee("""

content = content.replace(old, new)

with open('backend/database/migrate_json_to_mysql.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed employee email lookup')
