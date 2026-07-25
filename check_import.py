import sys
import os
print(f"CWD: {os.getcwd()}")
print(f"sys.path: {sys.path}")
try:
    import frontend.services.llm_service
    print(f"Module imported from: {frontend.services.llm_service.__file__}")
    print(f"Keys in module: {dir(frontend.services.llm_service)}")
    from frontend.services.llm_service import llm_service
    print("Import success!")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
