import streamlit as st
import os

def inject_css():
    """Reads and injects separated modular CSS files into the Streamlit app session."""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    css_dir = os.path.join(current_dir, "assets", "css")
    
    css_files = ["style.css", "cards.css", "forms.css", "tables.css", "animations.css"]
    combined_css = ""
    
    for filename in css_files:
        filepath = os.path.join(css_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                combined_css += f"\n/* --- {filename} --- */\n" + f.read()
                
    st.markdown(f"<style>{combined_css}</style>", unsafe_allow_html=True)
