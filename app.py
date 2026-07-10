import sys
import os
import subprocess

if __name__ == "__main__" and not any(arg.endswith("streamlit") or "streamlit" in arg for arg in sys.argv):
    print("Bootstrapping HirePilot Streamlit application...")
    cmd = [sys.executable, "-m", "streamlit", "run", "frontend/Dashboard.py"]
    subprocess.run(cmd)
else:
    try:
        import streamlit as st
        st.set_page_config(page_title="HirePilot - Redirect", layout="centered")
        st.warning("### ⚠️ Incorrect Streamlit Entrypoint")
        st.markdown("""
        To display the sidebar navigation and pages correctly, please run the application using:
        
        ```bash
        streamlit run frontend/Dashboard.py
        ```
        
        *If you ran `python app.py`, it should have bootstrapped automatically.*
        """)
        if st.button("Launch Correct Page Now"):
            subprocess.Popen([sys.executable, "-m", "streamlit", "run", "frontend/Dashboard.py"])
            st.success("Launched HirePilot on next port! Please check terminal.")
    except ImportError:
        print("Please install requirements and run: streamlit run frontend/Dashboard.py")
