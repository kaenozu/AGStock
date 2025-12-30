import sys

import streamlit as st

print(f"Streamlit version: {st.__version__}")
if hasattr(st, "rerun"):
    print("Has st.rerun(): YES")
else:
    print("Has st.rerun(): NO")

if hasattr(st, "experimental_rerun"):
    print("Has st.experimental_rerun(): YES")
else:
    print("Has st.experimental_rerun(): NO")
