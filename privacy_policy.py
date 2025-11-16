import streamlit as st
import os

def load_html(filepath: str) -> str:
    """Read the HTML file and return its contents as a string."""
    if not os.path.exists(filepath):
        return "<h3 style='color:red;'>Error: HTML file not found.</h3>"
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def privacy_policy_component(html_path: str):
    """
    Streamlit component for displaying the Privacy Policy HTML page.
    Usage:
        privacy_policy_component("privacy_policy.html")
    """
    st.title("📜 Privacy Policy — Dhaliwals Food Court")
    st.write("Unit of Param Mehar Enterprise — Proprietor: Pushpinder Singh Dhaliwal")
    st.markdown("---")

    html_content = load_html(html_path)

    st.components.v1.html(
        html_content,
        height=1500,
        scrolling=True
    )

# -------------------------------
# AUTO-RUN IF FILE EXECUTED DIRECTLY
# -------------------------------
if __name__ == "__main__":
    privacy_policy_component("privacy_policy.html")
