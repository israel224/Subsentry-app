import streamlit as st
import random
import requests
from datetime import datetime
from supabase import create_client, Client

# --- 1. DATABASE CONNECTION ---
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
    .card {
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #eee;
        margin-bottom: 15px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. EMAIL FUNCTION (BREVO) ---
def send_email(email, subject, content):
    headers = {
        "api-key": st.secrets["BREVO_API_KEY"],
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": "SubSentry", "email": "ekeledilichukwuisrael@gmail.com"},
        "to": [{"email": email}],
        "subject": subject,
        "htmlContent": content
    }
    try:
        requests.post("https://api.brevo.com/v3/smtp/email", json=payload, headers=headers)
    except:
        pass

# --- 4. APP LOGIC ---
if 'flow' not in st.session_state:
    st.session_state.flow = "landing"

# PAGE: LANDING
if st.session_state.flow == "landing":
    st.title("🔔 SUBSENTRY ALERT")
    st.write("Manage your subscriptions and get alerted before you get debited.")
    if st.button("CREATE ACCOUNT"):
        st.session_state.flow = "signup"
        st.rerun()
    if st.button("LOG IN"):
        st.session_state.flow = "login"
        st.rerun()

# PAGE: SIGNUP
elif st.session_state.flow == "signup":
    st.subheader("Create Account")
    email_in = st.text_input("Email Address")
    if st.button("SEND OTP"):
        if "@" in email_in:
            st.session_state.temp_email = email_in
            st.session_state.otp = str(random.randint(1000, 9999))
            otp_html = f"<h3>Your SubSentry Code is: {st.session_state.otp}</h3>"
            send_email(email_in, "Verification Code", otp_html)
            st.session_state.flow = "verify"
            st.rerun()

# PAGE: VERIFY
elif st.session_state.flow == "verify":
    st.subheader("Verify OTP")
    code_in = st.text_input("Enter 4-digit code")
    if st.button("VERIFY"):
        if code_in == st.session_state.otp:
            st.session_state.flow = "set_pass"
            st.rerun()
        else:
            st.error("Wrong code!")

# PAGE: SET PASSWORD
elif st.session_state.flow == "set_pass":
    st.subheader("Set Password")
    p1 = st.text_input("Password", type="password")
    if st.button("FINISH"):
        supabase.table("users").insert({"email": st.session_state.temp_email, "password": p1}).execute()
        st.success("Account Ready!")
        st.session_state.flow = "dashboard"
        st.rerun()

# PAGE: LOGIN
elif st.session_state.flow == "login":
    st.subheader("Login")
    l_email = st.text_input("Email")
    l_pass = st.text_input("Password", type="password")
    if st.button("ENTER"):
        res = supabase.table("users").select("*").eq("email", l_email).eq("password", l_pass).execute()
        if res.data:
            st.session_state.temp_email = l_email
            st.session_state.flow = "dashboard"
            st.rerun()
        else:
            st.error("Invalid credentials.")

# PAGE: DASHBOARD (THE NEW PART)
elif st.session_state.flow == "dashboard":
    st.title("🚀 Your Subscriptions")
    st.write(f"Logged in: *{st.session_state.temp_email}*")

    # ADD NEW SUB
    with st.expander("➕ Add New Subscription"):
        name = st.text_input("Service Name (e.g. Netflix)")
        amt = st.number_input("Price (₦)", min_value=0.0)
        date = st.date_input("Next Renewal Date")
        if st.button("SAVE"):
            sub_data = {
                "user_email": st.session_state.temp_email,
                "service_name": name,
                "price": amt,
                "renewal_date": str(date)
            }
            supabase.table("subscriptions").insert(sub_data).execute()
            st.success("Subscription Saved!")
            st.rerun()

    # DISPLAY SUBS
    res = supabase.table("subscriptions").select("*").eq("user_email", st.session_state.temp_email).execute()
    if res.data:
        for s in res.data:
            # Check for 2-day warning
            renewal = datetime.strptime(s['renewal_date'], '%Y-%m-%d').date()
            days_left = (renewal - datetime.now().date()).days
            
            warning_style = "color: red; font-weight: bold;" if days_left <= 2 else "color: green;"
            status = "⚠️ DUE SOON" if days_left <= 2 else f"{days_left} days left"

            st.markdown(f"""
                <div class="card">
                    <h3>{s['service_name']}</h3>
                    <p style="{warning_style}">{status}</p>
                    <p>Price: ₦{s['price']} | Date: {s['renewal_date']}</p>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No subscriptions added yet.")

    if st.button("LOG OUT"):
        st.session_state.flow = "landing"
        st.rerun()
