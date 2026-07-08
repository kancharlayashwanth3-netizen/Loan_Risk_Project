import streamlit as st
import sqlite3
import hashlib
import re
import random
import pandas as pd
import plotly.express as px

# ---------------------------
# DATABASE SETUP
# ---------------------------
def init_db():
    conn = sqlite3.connect("loan_risk.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            full_name TEXT,
            username TEXT PRIMARY KEY,
            password TEXT,
            mobile TEXT,
            email TEXT,
            pan TEXT UNIQUE,
            aadhaar TEXT UNIQUE,
            income REAL,
            employment TEXT,
            emi REAL,
            loan_amount REAL,
            cibil INTEGER,
            auth_loans INTEGER,
            unauth_loans INTEGER,
            risk_score REAL,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()


# ---------------------------
# SECURITY
# ---------------------------
def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ---------------------------
# VALIDATIONS
# ---------------------------
def valid_email(email):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email)


def valid_mobile(mobile):
    return re.match(r'^[6-9]\d{10-1}$', mobile)


def valid_pan(pan):
    return re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan)


def valid_aadhaar(aadhaar):
    return re.match(r'^\d{12}$', aadhaar)


# ---------------------------
# RISK ENGINE
# ---------------------------
def generate_cibil(income, emi, auth_loans, unauth_loans):
    score = 600

    if income > 500000:
        score += 80

    if income > 1000000:
        score += 50

    if emi < income * 0.3:
        score += 50

    score += auth_loans * 10
    score -= unauth_loans * 30

    return max(300, min(score, 900))


def calculate_risk(cibil, income, emi, employment):
    risk = 100

    risk -= (cibil / 10)

    if income > 1000000:
        risk -= 15
    elif income > 500000:
        risk -= 10

    if emi > income * 0.5:
        risk += 20

    if employment == "Government":
        risk -= 15
    elif employment == "Private":
        risk -= 5

    return max(0, min(risk, 100))


def loan_status(risk):
    if risk < 30:
        return "Approved"
    elif risk < 60:
        return "Review Required"
    else:
        return "Rejected"


# ---------------------------
# EMI CALCULATOR
# ---------------------------
def calculate_emi(principal, rate, tenure):
    monthly_rate = rate / (12 * 100)

    emi = (
        principal
        * monthly_rate
        * (1 + monthly_rate) ** tenure
    ) / (
        (1 + monthly_rate) ** tenure - 1
    )

    return round(emi, 2)


# ---------------------------
# APP CONFIG
# ---------------------------
st.set_page_config(page_title="AI Loan Risk Analytics", layout="wide")
st.markdown("""
<style>

/* FULL PAGE PROFESSIONAL BANKING BACKGROUND */
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    background-attachment: fixed;
}

/* MAIN CONTENT GLASS CARD */
.main .block-container {
    background: rgba(255, 255, 255, 0.08);
    padding: 2rem;
    border-radius: 25px;
    backdrop-filter: blur(12px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    color: white;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #141e30, #243b55);
}

/* TITLES */
h1, h2, h3, h4 {
    color: #FFD700 !important;
    text-align: center;
    font-family: Arial, sans-serif;
    font-weight: bold;
}

/* LABELS */
label, .stMarkdown, p {
    color: white !important;
    font-weight: 500;
}

/* INPUT BOXES */
.stTextInput input,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"] {
    background-color: rgba(255,255,255,0.95) !important;
    color: black !important;
    border-radius: 12px !important;
}

/* BUTTONS */
.stButton > button {
    background: linear-gradient(90deg, #FFD700, #FFA500);
    color: black;
    font-size: 16px;
    font-weight: bold;
    border-radius: 12px;
    border: none;
    width: 100%;
    transition: 0.3s ease;
}

.stButton > button:hover {
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    color: white;
    transform: scale(1.02);
}

/* METRIC BOXES */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.12);
    border-radius: 15px;
    padding: 15px;
    color: white;
}

/* TABLE */
[data-testid="stDataFrame"] {
    background-color: white;
    border-radius: 15px;
}

/* REMOVE STREAMLIT BRANDING */
footer, header {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)
init_db()

st.title("🏦 AI-Powered Loan Application Risk Analytics System")

menu = ["Register", "Login", "Admin Dashboard", "EMI Calculator"]
choice = st.sidebar.selectbox("Navigation", menu)


# ---------------------------
# SIMPLE REGISTER (100% EASY WORKING)
# REPLACE YOUR ENTIRE REGISTER SECTION WITH THIS
# ---------------------------
if choice == "Register":

    st.subheader("📝 User Registration")

    # USER INPUTS
    full_name = st.text_input("Full Name")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    mobile = st.text_input("Mobile Number")
    email = st.text_input("Email")
    pan = st.text_input("PAN Number")
    aadhaar = st.text_input("Aadhaar Number")

    income = st.number_input("Annual Income", min_value=1.0)

    employment = st.selectbox(
        "Employment Type",
        ["Government", "Private", "Business", "Self-Employed"]
    )

    emi = st.number_input(
        "Existing Monthly EMI",
        min_value=0.0
    )

    loan_amount = st.number_input(
        "Requested Loan Amount",
        min_value=1.0
    )

    # REGISTER BUTTON
    if st.button("Register"):

        # CLEAN INPUTS
        full_name = full_name.strip()
        username = username.strip()
        password = password.strip()
        mobile = mobile.strip()
        email = email.strip()
        pan = pan.strip().upper()
        aadhaar = aadhaar.strip()

        # VERY SIMPLE VALIDATION
        if full_name == "":
            st.error("Enter Full Name")

        elif username == "":
            st.error("Enter Username")

        elif password == "":
            st.error("Enter Password")

        elif mobile == "":
            st.error("Enter Mobile Number")

        elif email == "":
            st.error("Enter Email")

        elif pan == "":
            st.error("Enter PAN Number")

        elif aadhaar == "":
            st.error("Enter Aadhaar Number")

        else:
            # AUTO GENERATED LOAN DATA
            auth_loans = random.randint(0, 5)
            unauth_loans = random.randint(0, 3)

            # CIBIL + RISK
            cibil = generate_cibil(
                income,
                emi,
                auth_loans,
                unauth_loans
            )

            risk = calculate_risk(
                cibil,
                income,
                emi,
                employment
            )

            status = loan_status(risk)

            # DATABASE SAVE
            conn = sqlite3.connect("loan_risk.db")
            c = conn.cursor()

            try:
                c.execute(
                    """
                    INSERT INTO users
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        full_name,
                        username,
                        hash_pw(password),
                        mobile,
                        email,
                        pan,
                        aadhaar,
                        income,
                        employment,
                        emi,
                        loan_amount,
                        cibil,
                        auth_loans,
                        unauth_loans,
                        risk,
                        status
                    )
                )

                conn.commit()

                st.success("✅ Registration Successful!")
                st.success(f"Authorized Loans: {auth_loans}")
                st.success(f"Unauthorized Loans: {unauth_loans}")
                st.success(f"CIBIL Score: {cibil}")
                st.success(f"Loan Status: {status}")

                st.balloons()

            except sqlite3.IntegrityError:
                st.error(
                    "Username / PAN / Aadhaar already exists. Try different values."
                )

            conn.close()


# ---------------------------
# LOGIN (UPDATED WITH AUTHORIZED + UNAUTHORIZED LOANS)
elif choice == "Login":

    st.subheader("🔐 User Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        # CLEAN INPUT
        username = username.strip()
        password = password.strip()

        # DATABASE CONNECTION
        conn = sqlite3.connect("loan_risk.db")
        c = conn.cursor()

        c.execute(
            """
            SELECT * FROM users
            WHERE username=? AND password=?
            """,
            (username, hash_pw(password))
        )

        user = c.fetchone()

        conn.close()

        # LOGIN SUCCESS
        if user:

            st.success(f"Welcome {user[0]} 👋")

            # MAIN METRICS
            st.metric("CIBIL Score", user[11])
            st.metric("Risk Score", user[14])
            st.metric("Loan Status", user[15])

            # LOAN HISTORY
            st.write("### 📄 Loan History")

            st.write(
                f"**Authorized Loans Taken:** {user[12]}"
            )

            st.write(
                f"**Unauthorized / Missed Loans:** {user[13]}"
            )

            # PROFILE DETAILS
            st.write("### 👤 Profile Details")

            st.write(
                f"**Full Name:** {user[0]}"
            )

            st.write(
                f"**Mobile Number:** {user[3]}"
            )

            st.write(
                f"**Email:** {user[4]}"
            )

            st.write(
                f"**PAN Number:** {user[5]}"
            )

            st.write(
                f"**Aadhaar Number:** {user[6]}"
            )

            st.write(
                f"**Annual Income:** ₹{user[7]:,.2f}"
            )

            st.write(
                f"**Employment Type:** {user[8]}"
            )

            st.write(
                f"**Existing EMI:** ₹{user[9]:,.2f}"
            )

            st.write(
                f"**Requested Loan Amount:** ₹{user[10]:,.2f}"
            )

            # LOAN DECISION MESSAGE
            st.write("### 🏦 Loan Decision")

            if user[15] == "Approved":
                st.success(
                    "Congratulations! Your loan is approved."
                )

            elif user[15] == "Review Required":
                st.warning(
                    "Your profile needs manual review."
                )

            else:
                st.error(
                    "Loan rejected due to high risk."
                )

        # LOGIN FAILED
        else:
            st.error("Invalid Username or Password")

# ---------------------------
# ADMIN DASHBOARD
# ---------------------------
elif choice == "Admin Dashboard":

    st.subheader("📊 Admin Analytics Dashboard")

    conn = sqlite3.connect("loan_risk.db")
    df = pd.read_sql_query("SELECT * FROM users", conn)
    conn.close()

    if df.empty:
        st.warning("No user data available")

    else:
        st.metric("Total Users", len(df))
        st.metric(
            "Approved",
            len(df[df["status"] == "Approved"])
        )

        st.metric(
            "Rejected",
            len(df[df["status"] == "Rejected"])
        )

        fig1 = px.histogram(
            df,
            x="cibil",
            title="CIBIL Score Distribution"
        )

        st.plotly_chart(fig1, use_container_width=True)

        fig2 = px.pie(
            df,
            names="status",
            title="Loan Status Overview"
        )

        st.plotly_chart(fig2, use_container_width=True)

        fig3 = px.scatter(
            df,
            x="income",
            y="risk_score",
            color="status",
            title="Income vs Risk Score"
        )

        st.plotly_chart(fig3, use_container_width=True)

        st.dataframe(df)


# ---------------------------
# EMI CALCULATOR
# ---------------------------
elif choice == "EMI Calculator":

    st.subheader("💰 EMI Calculator")

    principal = st.number_input("Loan Amount", min_value=1.0)
    rate = st.number_input("Annual Interest Rate (%)", min_value=1.0)
    tenure = st.number_input("Tenure (Months)", min_value=1)

    if st.button("Calculate EMI"):

        emi_result = calculate_emi(
            principal,
            rate,
            tenure
        )

        st.success(f"Your Monthly EMI is ₹{emi_result}")