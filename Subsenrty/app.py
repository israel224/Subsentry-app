import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage

st.set_page_config(page_title="SubSentry AI", page_icon="🛡️")

# --- EMAIL FUNCTION ---
def send_sentry_alert(service_name, user_email):
    # This is the "Post Office" part of the code
    msg = EmailMessage()
    msg.set_content(f"🛡️ SubSentry Alert: Your {service_name} subscription expires in 2 days! Check your bank to avoid automatic debit.")
    msg['Subject'] = f"Action Required: {service_name} Renewal"
    msg['To'] = user_email
    msg['From'] = "subsentry.alerts@gmail.com" # We will configure this next

    # Note: Real sending requires your Google App Password (Step 2)
    st.info(f"📧 Simulated Email Sent to {user_email}: 'Cancel {service_name}?'")

if 'sub_data' not in st.session_state:
    st.session_state.sub_data = []

st.sidebar.title("🛡️ SubSentry Control")
user_email = st.sidebar.text_input("Your Alert Email", "example@gmail.com")
page = st.sidebar.radio("Navigate", ["Dashboard", "Add New Subscription"])

# --- DASHBOARD ---
if page == "Dashboard":
    st.title("📊 Subscription Command Center")
    
    if not st.session_state.sub_data:
        st.info("No active sentries.")
    else:
        df = pd.DataFrame(st.session_state.sub_data)
        today = datetime.now().date()
        
        for index, row in df.iterrows():
            expiry = datetime.strptime(row['Expiry Date'], "%Y-%m-%d").date()
            days_until = (expiry - today).days
            
            if days_until == 2:
                st.error(f"🚨 ALERT: {row['Service']} expires in 2 days!")
                if st.button(f"Send Alert Email for {row['Service']}"):
                    send_sentry_alert(row['Service'], user_email)
            
        st.divider()
        st.dataframe(df, use_container_width=True)

# --- ADD NEW ---
elif page == "Add New Subscription":
    st.title("➕ Deploy New Sentry")
    with st.form("entry_form"):
        name = st.text_input("Service Name")
        cost = st.number_input("Monthly Cost (₦)", min_value=0.0)
        pay_date = st.date_input("Payment Date")
        expiry_date = pay_date + timedelta(days=30)
        
        if st.form_submit_button("Start Guarding"):
            st.session_state.sub_data.append({
                "Service": name, "Cost": cost, "Expiry Date": str(expiry_date)
            })
            st.success(f"Tracking {name}. Expiry: {expiry_date}")