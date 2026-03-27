import streamlit as st
import pandas as pd
import random
import requests
from streamlit_gsheets import GSheetsConnection

# --- 1. THEME STYLING ---
st.set_page_config(page_title="SubSentry Alert", page_icon="🔔")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #000000; }
    div.stButton > button:first-child { 
        background-color: #007BFF; color: white; 
        border-radius: 5px; border: none; font-weight: bold; width: 100%;
    }
    .stTextInput input { background-color: #F8F9FA; color: #333333; border: 1px solid #CED4DA; }
    h1, h2, h3 { color: #333333 !important; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_users():
    try:
        # Read the sheet
        return conn.read(ttl=0)
    except:
        # Create structure if sheet is empty
        return pd.DataFrame(columns=["email", "password"])

# --- 3. CONFIG ---
BREVO_API_KEY = st.secrets["BREVO_API_KEY"]
SENDER_EMAIL = "ekeledilichukwuisrael@gmail.com"

def send_otp(email, code):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {"api-key": BREVO_API_KEY, "content-type": "application/json"}
    payload = {
        "sender": {"name": "SubSentry Alert", "email": SENDER_EMAIL},
        "to": [{"email": email}],
        "subject": "🔔 Your Verification Code",
        "htmlContent": f"<p>Your code is: <b>{code}</b></p>"
    }
    requests.post(url, json=payload, headers=headers)

# --- 4. APP FLOW ---
if 'flow' not in st.session_state:
    st.session_state.flow = "landing"

if st.session_state.flow == "landing":
    st.title("🔔 SUBSENTRY ALERT")
    if st.button("CREATE ACCOUNT (SIGN UP)"):
        st.session_state.flow = "signup_email"
        st.rerun()
    if st.button("LOG IN TO DASHBOARD"):
        st.session_state.flow = "login_screen"
        st.rerun()

elif st.session_state.flow == "signup_email":
    st.subheader("Sign Up")
    email_in = st.text_input("Enter Email")
    if st.button("SEND CODE"):
        st.session_state.temp_email = email_in
        st.session_state.otp = str(random.randint(100000, 999999))
        send_otp(email_in, st.session_state.otp)
        st.session_state.flow = "verify_code"
        st.rerun()

elif st.session_state.flow == "verify_code":
    st.subheader("Verify Email")
    code_in = st.text_input("Enter 6-digit code")
    if st.button("VERIFY"):
        if code_in == st.session_state.otp:
            st.session_state.flow = "create_password"
            st.rerun()
        else:
            st.error("Wrong code.")

elif st.session_state.flow == "create_password":
    st.subheader("Set Password")
    p1 = st.text_input("Password", type="password")
    if st.button("SAVE & FINISH"):
        # READ EXISTING DATA
        df = get_users()
        # ADD NEW USER
        new_data = pd.DataFrame([{"email": st.session_state.temp_email, "password": p1}])
        updated_df = pd.concat([df, new_data], ignore_index=True)
        # UPDATE THE SHEET
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success("Account Secured!")
        st.session_state.flow = "dashboard"
        st.rerun()

elif st.session_state.flow == "login_screen":
    st.subheader("Login")
    l_email = st.text_input("Email")
    l_pass = st.text_input("Password", type="password")
    if st.button("LOG IN"):
        df = get_users()
        if l_email in df['email'].values:
            user_row = df[df['email'] == l_email]
            if str(l_pass) == str(user_row['password'].values[0]):
                st.session_state.temp_email = l_email
                st.session_state.flow = "dashboard"
                st.rerun()
            else: st.error("Wrong password")
        else: st.error("Email not found")

elif st.session_state.flow == "dashboard":
    st.title(f"🚀 Welcome, {st.session_state.temp_email}")
    st.info("You are logged in and your data is saved in Google Sheets.")
    if st.button("LOGOUT"):
        st.session_state.flow = "landing"
        st.rerun()
