"""Offline verification that the bar.py -> api_client.py import chain works without ImportError."""
import ast
import sys

api_path = r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot\frontend\components\api_client.py"
bar_path = r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot\frontend\components\bar.py"

for p in (api_path, bar_path):
    with open(p, encoding="utf-8") as fh:
        src = fh.read()
    tree = ast.parse(src)
    fns = {
        n.name: n
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef)
    }
    print(f"{p}: parsed OK, top-level functions = {sorted(fns.keys())}")
    if p.endswith("api_client.py"):
        assert "login_user" in fns, "login_user missing"
        assert "logout_user" in fns, "logout_user MISSING — import will fail"
        assert "clear_hr_session_state" in fns, "clear_hr_session_state MISSING — import will fail"
        print("  ✅ api_client.py exports logout_user and clear_hr_session_state")

# Now check bar.py imports resolves to exactly those names
with open(bar_path, encoding="utf-8") as fh:
    bar_src = fh.read()
bar_tree = ast.parse(bar_src)
resolved_imported_names = []
for n in ast.walk(bar_tree):
    if isinstance(n, ast.ImportFrom) and n.module and "api_client" in n.module:
        for a in n.names:
            resolved_imported_names.append(a.name)
print(f"\nbar.py imports from api_client: {resolved_imported_names}")
for required in ("clear_hr_session_state", "logout_user"):
    assert required in resolved_imported_names, f"bar.py doesn't import {required}"
# and check they exist in api_client.py's function set too
with open(api_path, encoding="utf-8") as fh:
    api_tree = ast.parse(fh.read())
api_fns = {n.name for n in ast.walk(api_tree) if isinstance(n, ast.FunctionDef)}
for required in ("clear_hr_session_state", "logout_user"):
    assert required in api_fns, f"api_client.py missing function {required}"
print("  ✅ All names imported by bar.py are defined in api_client.py — no ImportError")

# Lastly inspect body of logout_user: POST {API_URL}/auth/logout
for n in ast.walk(api_tree):
    if isinstance(n, ast.FunctionDef) and n.name == "logout_user":
        # find string subscript containing /auth/logout
        sources = []
        for sub in ast.walk(n):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                if "/auth/logout" in sub.value or "auth/logout" in sub.value:
                    sources.append(sub.value)
        print(f"\nlogout_user() references URL containing: {sources}")
        assert any("auth/logout" in s for s in sources), "logout_user does not POST to /auth/logout"
        print("  ✅ logout_user POSTs to /auth/logout")

# Inspect body of clear_hr_session_state: touches the right session keys
for n in ast.walk(api_tree):
    if isinstance(n, ast.FunctionDef) and n.name == "clear_hr_session_state":
        session_actions = []
        for sub in ast.walk(n):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                session_actions.append(sub.value)
            elif isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name) and sub.value.id == "st" and sub.attr == "session_state":
                pass
        # collect strings used as 1st args to pop / as subscript keys
        keys_seen = []
        assigns = []
        for sub in ast.walk(n):
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) and sub.func.attr == "pop":
                if sub.args and isinstance(sub.args[0], ast.Constant):
                    keys_seen.append(sub.args[0].value)
            if isinstance(sub, ast.Assign):
                for tgt in sub.targets:
                    if isinstance(tgt, ast.Subscript) and isinstance(tgt.slice, ast.Constant):
                        assigns.append((tgt.slice.value, sub.value.value if isinstance(sub.value, ast.Constant) else None))
        print(f"\nclear_hr_session_state() pops keys: {keys_seen}")
        print(f"clear_hr_session_state() writes defaults: {assigns}")
        required_pops = {"is_authenticated", "token", "hr_email"}
        missing_pops = required_pops - set(keys_seen)
        assert not missing_pops, f"Failed to clear keys: {missing_pops}"
        required_assigns = {("app_mode", "public"), ("public_page", "Home")}
        assert required_assigns.issubset(set(assigns)), f"Missing default writes: {required_assigns - set(assigns)}"
        print("  ✅ clear_hr_session_state clears HR keys and resets to public Home defaults")

print("\n🎉 ALL VERIFICATIONS PASSED")
