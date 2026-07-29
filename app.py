import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Page Configuration
st.set_page_config(page_title="Electric Glove Proof Testing System", layout="wide")

# --- CUSTOM CSS FOR BLUE, WHITE & LIGHT BLUE THEME & BACKGROUND ---
st.markdown("""
    <style>
    /* Main Background & Theme Styling */
    .stApp {
        background-color: #F0F8FF; /* Alice Blue / Light Blue tint */
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #E6F2FF;
        border-right: 2px solid #B0E0E6;
    }
    
    /* Headers Styling */
    h1, h2, h3 {
        color: #003366 !important; /* Dark Blue */
    }
    
    /* Buttons Styling */
    .stButton>button {
        background-color: #0066CC;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #004080;
        color: #ffffff;
    }
    
    /* Login Screen Background Styling */
    .login-container {
        background: linear-gradient(rgba(0, 51, 102, 0.7), rgba(0, 102, 204, 0.7)), 
                    url('https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=1500&q=80');
        background-size: cover;
        background-position: center;
        padding: 40px;
        border-radius: 15px;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Session State for Data Storage
if 'users' not in st.session_state:
    st.session_state['users'] = {
        "admin": {"password": "123", "role": "Admin"},
        "supervisor": {"password": "123", "role": "Supervisor"},
        "operator": {"password": "123", "role": "Operator"}
    }

if 'orders' not in st.session_state:
    st.session_state['orders'] = pd.DataFrame(columns=[
        'Month', 'Order Name', 'Order No', 'Target Qty'
    ])

if 'test_entries' not in st.session_state:
    st.session_state['test_entries'] = pd.DataFrame(columns=[
        'Date', 'Month', 'Order No', 'Machine Number', 
        'Left Pass', 'Right Pass', 'Left Fail', 'Right Fail', 
        'Pass Pairs', 'Total Fail', 'Logged User', 'Remarks'
    ])

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['role'] = ""

# --- 1. LOGIN MODULE WITH BACKGROUND IMAGE CONTAINER ---
def login_screen():
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.title("⚡ Electric Glove Proof Testing System")
    st.markdown("### Secure Login Portal")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username (e.g. admin / supervisor / operator)")
        password = st.text_input("Password", type="password")
        
        if st.button("🔐 Login to System"):
            if username in st.session_state['users'] and st.session_state['users'][username]['password'] == password:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['role'] = st.session_state['users'][username]['role']
                st.success(f"Welcome {username.capitalize()}!")
                st.rerun()
            else:
                st.error("Invalid Username or Password!")
    
    with col2:
        st.info("**Default Logins:**\n- Admin: `admin` / `123`\n- Supervisor: `supervisor` / `123`\n- Operator: `operator` / `123`")
    st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state['logged_in']:
    login_screen()
else:
    # Sidebar Navigation with Icons and Buttons (Replacing Dropdown)
    st.sidebar.title(f"👤 User: {st.session_state['username'].capitalize()}")
    st.sidebar.write(f"Role: **{st.session_state['role']}**")
    st.sidebar.markdown("---")
    
    st.sidebar.subheader("📌 Navigation Menu")
    
    if 'menu_choice' not in st.session_state:
        st.session_state['menu_choice'] = "Dashboard"

    if st.sidebar.button("📊 Dashboard", use_container_width=True):
        st.session_state['menu_choice'] = "Dashboard"
    if st.sidebar.button("📦 Order & Plan Mgmt", use_container_width=True):
        st.session_state['menu_choice'] = "Order Management"
    if st.sidebar.button("🧪 Glove Test Entry", use_container_width=True):
        st.session_state['menu_choice'] = "Test Entry"
    if st.sidebar.button("📈 Reports & Progress", use_container_width=True):
        st.session_state['menu_choice'] = "Reports"
    
    role = st.session_state['role']
    if role == "Admin":
        if st.sidebar.button("👥 User Management", use_container_width=True):
            st.session_state['menu_choice'] = "User Management"

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

    choice = st.session_state['menu_choice']

    # --- 2. ORDER & MONTHLY PLAN MANAGEMENT ---
    if choice == "Order Management":
        st.header("📦 Monthly Order & Plan Management")
        
        if role in ["Admin", "Supervisor"]:
            tab1, tab2 = st.tabs(["➕ Add Monthly Plan / Order", "➕ Add Extra Single Order"])
            
            with tab1:
                st.info("මාසික සැලසුම් (Monthly Plans) සහ ඇණවුම් ඇතුළත් කිරීම (මාසයෙන් මාසයට වෙන වෙනම ගබඩා වේ).")
                with st.form("monthly_plan_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        selected_month = st.selectbox("Select Month & Year", ["January 2026", "February 2026", "March 2026", "April 2026", "May 2026", "June 2026", "July 2026", "August 2026", "September 2026", "October 2026", "November 2026", "December 2026"])
                        order_name = st.text_input("Order Name / Customer Name")
                    with col2:
                        order_no = st.text_input("Order Number (Unique)")
                        target_qty = st.number_input("Target Quantity (Glove Pairs)", min_value=1, value=100)
                    
                    submit_plan = st.form_submit_button("Save Monthly Order")
                    if submit_plan:
                        if order_name and order_no:
                            new_row = pd.DataFrame({
                                'Month': [selected_month],
                                'Order Name': [str(order_name)],
                                'Order No': [str(order_no)],
                                'Target Qty': [int(target_qty)]
                            })
                            st.session_state['orders'] = pd.concat([st.session_state['orders'], new_row], ignore_index=True)
                            st.success(f"Order for {selected_month} added successfully!")
                        else:
                            st.warning("Please fill Order Name and Order No.")
            
            with tab2:
                st.info("හදිසි හෝ අමතර Orders (Extra Orders) වෙනම එකතු කරගැනීමට.")
                with st.form("extra_order_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        ex_month = st.selectbox("Select Month for Extra Order", ["January 2026", "February 2026", "March 2026", "April 2026", "May 2026", "June 2026", "July 2026", "August 2026", "September 2026", "October 2026", "November 2026", "December 2026"])
                        ex_cust = st.text_input("Extra Order Name / Client")
                    with col2:
                        ex_no = st.text_input("Extra Order Number")
                        ex_qty = st.number_input("Extra Quantity", min_value=1, value=50)
                    
                    submit_ex = st.form_submit_button("Add Extra Order")
                    if submit_ex:
                        if ex_cust and ex_no:
                            new_ex = pd.DataFrame({
                                'Month': [ex_month],
                                'Order Name': [str(ex_cust) + " (Extra)"],
                                'Order No': [str(ex_no)],
                                'Target Qty': [int(ex_qty)]
                            })
                            st.session_state['orders'] = pd.concat([st.session_state['orders'], new_ex], ignore_index=True)
                            st.success("Extra Order added successfully!")
                        else:
                            st.warning("Please fill required fields.")
        
        st.subheader("📋 Existing Orders & Plans List")
        if not st.session_state['orders'].empty:
            all_months = st.session_state['orders']['Month'].unique()
            filter_m = st.selectbox("Filter Orders by Month", all_months)
            filtered_orders = st.session_state['orders'][st.session_state['orders']['Month'] == filter_m]
            
            st.dataframe(filtered_orders, use_container_width=True)
            
            if role == "Admin" and st.button("Clear All Orders Data"):
                st.session_state['orders'] = pd.DataFrame(columns=st.session_state['orders'].columns)
                st.success("All orders cleared.")
                st.rerun()
        else:
            st.info("No orders or plans found yet.")

    # --- 3. TEST ENTRY (MACHINE NUMBER & PASS PAIRS) ---
    elif choice == "Test Entry":
        st.header("🧪 Electric Glove Proof Testing Entry")
        
        orders_df = st.session_state['orders']
        if orders_df.empty:
            st.warning("Please add monthly orders/plans in 'Order & Plan Mgmt' first!")
        else:
            with st.form("test_form"):
                col1, col2 = st.columns(2)
                with col1:
                    test_date = st.date_input("Test Date", datetime.today())
                    
                    available_months = orders_df['Month'].unique()
                    sel_test_month = st.selectbox("Select Month", available_months)
                    
                    month_orders = orders_df[orders_df['Month'] == sel_test_month]
                    if month_orders.empty:
                        st.warning("No orders found for this month.")
                        order_no_sel = ""
                    else:
                        order_no_sel = st.selectbox("Select Order No", month_orders['Order No'].unique())
                        match_cust = month_orders[month_orders['Order No'] == order_no_sel]['Order Name'].values
                        cust_name = match_cust[0] if len(match_cust) > 0 else ""
                        st.write(f"Order Name: **{cust_name}**")
                    
                    machine_no = st.selectbox("Machine Number", ["Machine 01", "Machine 02", "Machine 03", "Machine 04", "Machine 05"])
                
                with col2:
                    l_pass = st.number_input("Left Hand Pass Qty", min_value=0, value=0)
                    r_pass = st.number_input("Right Hand Pass Qty", min_value=0, value=0)
                    l_fail = st.number_input("Left Hand Fail Qty", min_value=0, value=0)
                    r_fail = st.number_input("Right Hand Fail Qty", min_value=0, value=0)
                    remarks = st.text_input("Remarks / Safety Notes")
                
                submit_test = st.form_submit_button("Save Test Entry")
                if submit_test:
                    if order_no_sel:
                        pass_pairs = min(l_pass, r_pass)  # Good pairs changed to Pass Pairs
                        total_fail = l_fail + r_fail
                        logged_user = st.session_state['username']
                        
                        new_test = pd.DataFrame({
                            'Date': [str(test_date)],
                            'Month': [sel_test_month],
                            'Order No': [order_no_sel],
                            'Machine Number': [machine_no],
                            'Left Pass': [l_pass],
                            'Right Pass': [r_pass],
                            'Left Fail': [l_fail],
                            'Right Fail': [r_fail],
                            'Pass Pairs': [pass_pairs],
                            'Total Fail': [total_fail],
                            'Logged User': [logged_user],
                            'Remarks': [remarks]
                        })
                        st.session_state['test_entries'] = pd.concat([st.session_state['test_entries'], new_test], ignore_index=True)
                        st.success(f"Test saved successfully! Pass Pairs calculated: {pass_pairs}")
                    else:
                        st.error("Please select a valid Order No.")

        st.subheader("📋 Recent Glove Test Entries")
        if not st.session_state['test_entries'].empty:
            st.dataframe(st.session_state['test_entries'], use_container_width=True)
        else:
            st.info("No test entries recorded yet.")

    # --- 4. USER MANAGEMENT (ADMIN ONLY) ---
    elif choice == "User Management" and role == "Admin":
        st.header("👥 Operator & User Management")
        st.markdown("නව ඔපරේටර්වරුන් හෝ යූසර්වරුන් එකතු කිරීම සඳහා පහත පෝරමය භාවිතා කරන්න.")
        
        with st.form("add_user_form"):
            new_username = st.text_input("New Username")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Select Role", ["Operator", "Supervisor", "Admin"])
            
            submit_user = st.form_submit_button("➕ Add New User")
            if submit_user:
                if new_username and new_password:
                    if new_username in st.session_state['users']:
                        st.warning("මෙම Username එක දැනටමත් පවතී!")
                    else:
                        st.session_state['users'][new_username] = {
                            "password": new_password,
                            "role": new_role
                        }
                        st.success(f"Operator ({new_username}) සාර්ථකව එකතු කරන ලදී!")
                else:
                    st.warning("කරුණාකර Username සහ Password ඇතුළත් කරන්න.")
        
        st.subheader("📋 Current System Operators / Users")
        users_data = []
        for uname, uinfo in st.session_state['users'].items():
            users_data.append({"Username": uname, "Role": uinfo["role"]})
        
        users_df = pd.DataFrame(users_data)
        st.dataframe(users_df, use_container_width=True)

    # --- 5. DASHBOARD ---
    elif choice == "Dashboard":
        st.header("📊 Electric Glove Testing Dashboard")
        
        orders_df = st.session_state['orders']
        tests_df = st.session_state['test_entries']
        
        total_orders = len(orders_df)
        total_target_qty = orders_df['Target Qty'].astype(int).sum() if not orders_df.empty else 0
        total_pass_pairs = tests_df['Pass Pairs'].astype(int).sum() if not tests_df.empty else 0
        total_fails = tests_df['Total Fail'].astype(int).sum() if not tests_df.empty else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Order Entries", total_orders)
        col2.metric("Target Glove Qty", total_target_qty)
        col3.metric("Total Tested Pass Pairs", total_pass_pairs)
        col4.metric("Total Defective Fails", total_fails)
        
        st.markdown("---")
        st.subheader("📈 Monthly Testing Summary Chart")
        if not tests_df.empty:
            chart_data = tests_df.groupby('Month')[['Pass Pairs', 'Total Fail']].sum()
            st.bar_chart(chart_data)
        else:
            st.info("Charts will appear once test entries are added.")

    # --- 6. REPORTS & PROGRESS (MONTH-WISE TARGET VS TESTED VS REMAINING) ---
    elif choice == "Reports":
        st.header("📈 Monthly Reports & Progress Tracking")
        
        orders_df = st.session_state['orders']
        tests_df = st.session_state['test_entries']
        
        if not orders_df.empty or not tests_df.empty:
            st.subheader("🗓️ Month-wise Order vs Tested vs Remaining Progress")
            
            all_available_months = sorted(list(set(orders_df['Month'].tolist() + tests_df['Month'].tolist()))) if not orders_df.empty else tests_df['Month'].unique()
            report_month = st.selectbox("Select Month for Report", all_available_months)
            
            m_orders = orders_df[orders_df['Month'] == report_month] if not orders_df.empty else pd.DataFrame()
            m_tests = tests_df[tests_df['Month'] == report_month] if not tests_df.empty else pd.DataFrame()
            
            summary_list = []
            if not m_orders.empty:
                for idx, row in m_orders.iterrows():
                    ord_no = row['Order No']
                    ord_name = row['Order Name']
                    target = int(row['Target Qty'])
                    
                    ord_tests = m_tests[m_tests['Order No'] == ord_no] if not m_tests.empty else pd.DataFrame()
                    tested_qty = int(ord_tests['Pass Pairs'].sum() + ord_tests['Total Fail'].sum()) if not ord_tests.empty else 0
                    passed_qty = int(ord_tests['Pass Pairs'].sum()) if not ord_tests.empty else 0
                    remaining_qty = max(0, target - tested_qty)
                    
                    summary_list.append({
                        'Order No': ord_no,
                        'Order Name': ord_name,
                        'Target Qty': target,
                        'Tested Qty': tested_qty,
                        'Pass Pairs': passed_qty,
                        'Remaining Qty to Test': remaining_qty
                    })
            
            if summary_list:
                summary_df = pd.DataFrame(summary_list)
                st.dataframe(summary_df, use_container_width=True)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    summary_df.to_excel(writer, index=False, sheet_name='Monthly_Progress_Report')
                    if not m_tests.empty:
                        m_tests.to_excel(writer, index=False, sheet_name='Detailed_Test_Logs')
                excel_data = output.getvalue()
                
                st.download_button(
                    label=f"📥 Download {report_month} Report as Excel",
                    data=excel_data,
                    file_name=f"Glove_Testing_Report_{report_month.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("No orders found for the selected month.")
                
            st.subheader("📋 Detailed Test Log Entries (Machine Number & Logged User)")
            if not m_tests.empty:
                st.dataframe(m_tests, use_container_width=True)
            else:
                st.info("No test records for this month.")
        else:
            st.info("No data available to generate reports.")