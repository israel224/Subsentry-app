import streamlit as st
import random
import requests
from supabase import create_client, Client

# --- 1. DATABASE CONNECTION ---
# This connects to the Supabase URL and Key you just put in your Secrets
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Database credentials missing in Streamlit Secrets.")
    st.stop()

# --- 2. STYLING ---
st.set_page_config(page_title="SubSentry Alert", page_icon="🔔")
st.markdown("""
    <style>
    .stApp { background-color: white; color: black; }
    div.stButton > button { 
        background-color: #007BFF; 
        color: white; 
        width: 100%; 
        border-radius: 5px; 
        font-weight: bold; 
        border: none;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. EMAIL FUNCTION (BREVO) ---
def send_otp(email, code):
    headers = {
        "api-key": st.secrets["BREVO_API_KEY"],
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": "SubSentry", "email": "ekeledilichukwuisrael@gmail.com"},
        "to": [{"email": email}],
        "subject": "Your SubSentry Verification Code",
        "htmlContent": f"""
            <h3>Welcome to SubSentry</h3>
            <p>Your verification code is: <b style='font-size: 20px; color: #007BFF;'>{code}</b></p>
            <p>If you didn't request this, please ignore this email.</p>
        """
    }
    try:
        response = requests.post("https://api.brevo.com/v3/smtp/email", json=payload, headers=headers)
        return response.status_code == 201
    except:
        return False

# --- 4. APP LOGIC ---
if 'flow' not in st.session_state:
    st.session_state.flow = "landing"

# PAGE: LANDING
if st.session_state.flow == "landing":
    st.title("🔔 SUBSENTRY ALERT")
    st.write("Never miss a subscription renewal again.")
    if st.button("CREATE ACCOUNT"):
        st.session_state.flow = "signup"
        st.rerun()
    if st.button("LOG IN"):
        st.session_state.flow = "login"
        st.rerun()

# PAGE: SIGNUP (EMAIL INPUT)
elif st.session_state.flow == "signup":
    st.subheader("Create your account")
    email_in = st.text_input("Enter your email address")
    if st.button("SEND VERIFICATION CODE"):
        if "@" in email_in:
            st.session_state.temp_email = email_in
            st.session_state.otp = str(random.randint(1000, 9999))
            if send_otp(email_in, st.session_state.otp):
                st.session_state.flow = "verify"
                st.success("Code sent! Check your inbox.")
                st.rerun()
            else:
                st.error("Failed to send email. Check your Brevo API key.")
        else:
            st.error("Please enter a valid email.")

# PAGE: VERIFY OTP
elif st.session_state.flow == "verify":
    st.subheader("Verify your email")
    code_in = st.text_input("Enter 4-digit code")
    if st.button("VERIFY"):
        if code_in == st.session_state.otp:
            st.session_state.flow = "set_pass"
            st.rerun()
        else:
            st.error("Invalid code. Please try again.")

# PAGE: SET PASSWORD & SAVE TO SUPABASE
elif st.session_state.flow == "set_pass":
    st.subheader("Secure your account")
    p1 = st.text_input("Create a password", type="password")
    if st.button("COMPLETE SIGNUP"):
        if len(p1) > 5:
            # This part sends the data to your Supabase table
            user_data = {"email": st.session_state.temp_email, "password": p1}
            try:
                supabase.table("users").insert(user_data).execute()
                st.success("Account created successfully!")
                st.session_state.flow = "dashboard"
                st.rerun()
            except Exception as e:
                st.error(f"Error saving to database: {e}")
        else:
            st.error("Password must be at least 6 characters.")

# PAGE: LOGIN
elif st.session_state.flow == "login":
    st.subheader("Welcome back")
    l_email = st.text_input("Email")
    l_pass = st.text_input("Password", type="password")
    if st.button("LOG IN"):
        # This checks the Supabase table for the user
        res = supabase.table("users").select("*").eq("email", l_email).execute()
        if res.data and res.data[0]['password'] == l_pass:
            st.session_state.temp_email = l_email
            st.session_state.flow = "dashboard"
            st.rerun()
        else:
            st.error("Invalid email or password.")

# PAGE: DASHBOARD
elif st.session_state.flow == "dashboard":
    st.title(f"🚀 Hello, {st.session_state.temp_email}")
    st.write("Welcome to your SubSentry dashboard.")
    st.info("Currently tracking: 0 Subscriptions")
    if st.button("LOG OUT"):
        st.session_state.flow = "landing"
        st.rerun()
