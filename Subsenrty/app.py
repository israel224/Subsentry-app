import streamlit as st
import pandas as pd
import random
import requests

# --- 1. THEME ---
st.set_page_config(page_title="SubSentry Alert", page_icon="🔔")
st.markdown("<style>.stApp { background-color: white; color: black; }</style>", unsafe_allow_html=True)

# --- 2. CONFIG ---
# Replace this URL with your Google Form "Submit" link if the Sheet method fails
FORM_URL = "https://docs.google.com/forms/d/e/YOUR_FORM_ID/formResponse"

# --- 3. APP FLOW ---
if 'flow' not in st.session_state: st.session_state.flow = "landing"

if st.session_state.flow == "landing":
    st.title("🔔 SUBSENTRY ALERT")
    if st.button("CREATE ACCOUNT"): st.session_state.flow = "signup"; st.rerun()
    if st.button("LOG IN"): st.session_state.flow = "login"; st.rerun()

elif st.session_state.flow == "signup":
    email = st.text_input("Enter Email")
    if st.button("SEND CODE"):
        st.session_state.temp_email = email
        st.session_state.otp = str(random.randint(1000, 9999))
        # (Send OTP code here as before)
        st.session_state.flow = "verify"; st.rerun()

elif st.session_state.flow == "pass":
    p1 = st.text_input("New Password", type="password")
    if st.button("SAVE & FINISH"):
        # This sends data directly without needing complex permissions
        data = {"entry.123456": st.session_state.temp_email, "entry.789012": p1}
        requests.post(FORM_URL, data=data)
        st.success("Account Secured!")
        st.session_state.flow = "dashboard"; st.rerun()
