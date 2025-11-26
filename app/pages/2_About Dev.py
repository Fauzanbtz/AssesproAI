import streamlit as st
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent

st.set_page_config(page_title="About Dev", layout="wide")

st.title("Developer Team Information")

st.markdown("""
### **Team ID:** A25-CS348  
---

### **Members**

#### **1. Muhamad Aditya Umar Faiz**  
- **Cohort ID:** M891D5Y1168  

#### **2. Muhammad Fauzan**  
- **Cohort ID:** M891D5Y1270  

#### **3. Andi Nabilah Putri Maharani**  
- **Cohort ID:** M891D5X0211  
""")

# ===== Banner / Image =====
img_path = APP_DIR / "dev.png"

if img_path.exists():
    st.image(str(img_path), use_container_width=True)
else:
    st.info(f"dev.png not found in {img_path}")


