import streamlit as st
import pandas as pd
import random
import requests
from streamlit_gsheets import GSheetsConnection

# --- 1. THEME ---
st.set_page_config(page_title="SubSentry Alert", page_icon="🔔")
st.markdown("<style>.stApp { background-color: white; color: black; } div.stButton > button { background-color: #007BFF; color: white; border-radius: 5px; }</style>", unsafe_allow_html=True)

# --- 2. DATABASE ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_users():
    try:
        # We read the sheet data
        return conn.read(worksheet="Sheet1", ttl=0)
    except:
        return pd.DataFrame(columns=["email", "password"])

# --- 3. CONFIG ---
BREVO_API_KEY = st.secrets["BREVO_API_KEY"]
SENDER_EMAIL = "ekeledilichukwuisrael@gmail.com"

def send_otp(email, code):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {"api-key": BREVO_API_KEY, "content-type": "application/json"}
    payload = {"sender": {"name": "SubSentry", "email": SENDER_EMAIL}, "to": [{"email": email}], "subject": "Your Code", "htmlContent": f"<b>{code}</b>"}
    requests.post(url, json=payload, headers=headers)

# --- 4. APP FLOW ---
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
        send_otp(email, st.session_state.otp)
        st.session_state.flow = "verify"; st.rerun()

elif st.session_state.flow == "verify":
    code = st.text_input("Enter Code")
    if st.button("VERIFY"):
        if code == st.session_state.otp: st.session_state.flow = "pass"; st.rerun()
        else: st.error("Wrong code")

elif st.session_state.flow == "pass":
    p1 = st.text_input("New Password", type="password")
    if st.button("SAVE & FINISH"):
        # GET CURRENT USERS
        df = get_users()
        # ADD NEW USER
        new_user = pd.DataFrame([{"email": st.session_state.temp_email, "password": p1}])
        updated_df = pd.concat([df, new_user], ignore_index=True)
        
        # THE FIX: This is a more stable way to update
        try:
            conn.update(worksheet="Sheet1", data=updated_df)
            st.success("Account Secured!")
            st.session_state.flow = "dashboard"
            st.rerun()
        except Exception as e:
            st.error(f"Almost there! Just hit 'SAVE & FINISH' one more time. (Error: {e})")

elif st.session_state.flow == "login":
    l_email = st.text_input("Email")
    l_pass = st.text_input("Password", type="password")
    if st.button("ENTER"):
        df = get_users()
        if not df.empty and l_email in df['email'].values:
            # Match the password
            stored_pass = str(df[df['email'] == l_email]['password'].values[0])
            if str(l_pass) == stored_pass:
                st.session_state.temp_email = l_email
                st.session_state.flow = "dashboard"; st.rerun()
            else: st.error("Wrong Password")
        else: st.error("Account not found")

elif st.session_state.flow == "dashboard":
    st.success(f"Welcome {st.session_state.temp_email}!")
    if st.button("LOGOUT"): st.session_state.flow = "landing"; st.rerun()
