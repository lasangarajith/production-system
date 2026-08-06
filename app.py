import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import os
import io

# Page Configuration
st.set_page_config(page_title="Electric Glove Proof Testing System", page_icon="⚡", layout="wide")

# --- DATABASE SETUP (SQLite with absolute path to prevent data loss) ---
def init_db():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'glove_system.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    
    # Orders Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT,
            order_name TEXT,
            order_no TEXT,
            product_code TEXT,
            target_qty INTEGER
        )
    ''')
    
    # Test Entries Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            month TEXT,
            order_no TEXT,
            product_code TEXT,
            machine_number TEXT,
            left_pass INTEGER,
            right_pass INTEGER,
            left_fail INTEGER,
            right_fail INTEGER,
            tested_pairs REAL,
            pass_pairs REAL,
            total_fail INTEGER,
            logged_user TEXT,
            remarks TEXT
        )
    ''')
    
    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT
        )
    ''')
    
    # Default Users
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users VALUES ('admin', '123', 'Admin')")
        cursor.execute("INSERT INTO users VALUES ('supervisor', '123', 'Supervisor')")
        cursor.execute("INSERT INTO users VALUES ('operator', '123', 'Operator')")
    
    conn.commit()
    return conn

conn = init_db()

# Safe DataFrame loader for orders to handle column name discrepancies
def load_orders_safe(conn):
    try:
        df = pd.read_sql("SELECT * FROM orders", conn)
        if 'target_qty' not in df.columns and 'order_qty' in df.columns:
            df.rename(columns={'order_qty': 'target_qty'}, inplace=True)
        elif 'target_qty' not in df.columns and len(df.columns) >= 6:
            df.columns = ['id', 'month', 'order_name', 'order_no', 'product_code', 'target_qty'] + list(df.columns[6:])
        return df
    except Exception:
        return pd.DataFrame(columns=['id', 'month', 'order_name', 'order_no', 'product_code', 'target_qty'])

# --- PERSISTENT SESSION STATE WITH QUERY PARAMS ---
query_params = st.query_params

if 'logged_in' not in st.session_state:
    if "user" in query_params and "role" in query_params:
        st.session_state['logged_in'] = True
        st.session_state['username'] = query_params["user"]
        st.session_state['role'] = query_params["role"]
    else:
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        st.session_state['role'] = ""

# --- MODERN STYLING & CUSTOM CSS ---
if not st.session_state['logged_in']:
    st.markdown("""
        <style>
        .stApp { 
            background: linear-gradient(135deg, #1e1b4b 0%, #311042 50%, #0f172a 100%), 
                        url('https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=1500&q=80');
            background-blend-mode: overlay;
            background-size: cover; 
            background-position: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
        }
        .login-card {
            background-color: #ffffff;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
            max-width: 450px;
            margin: 0 auto;
            color: #1e293b;
        }
        .stButton>button { 
            background-color: #7c3aed; 
            color: white; 
            border-radius: 8px; 
            font-weight: bold; 
            border: none;
            padding: 0.5rem 1rem;
            box-shadow: 0 4px 6px -1px rgba(124, 58, 237, 0.3);
            width: 100%;
        }
        .stButton>button:hover { background-color: #6d28d9; color: white; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .stApp { 
            background-color: #f8fafc;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
        }
        [data-testid="stSidebar"] { 
            background: linear-gradient(180deg, #0d1b2a 0%, #1b263b 100%); 
            color: #ffffff;
            border-right: 1px solid #334155;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { 
            color: #ffffff !important; 
        }
        
        /* Sidebar Navigation Buttons */
        [data-testid="stSidebar"] div.stButton > button {
            width: 100% !important;
            background-color: #162238 !important;
            color: #ffffff !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            border: 2px solid #00f0ff !important;
            padding: 0.5rem 1rem !important;
            box-shadow: 0 0 12px rgba(0, 240, 255, 0.25) !important;
            text-align: left !important;
            transition: all 0.3s ease-in-out !important;
        }
        
        [data-testid="stSidebar"] div.stButton > button:hover {
            background-color: #0b1329 !important;
            color: #00f0ff !important;
            border-color: #00f0ff !important;
            box-shadow: 0 0 18px rgba(0, 240, 255, 0.6) !important;
        }

        [data-testid="stSidebar"] div.stButton > button:active,
        [data-testid="stSidebar"] div.stButton > button:focus {
            background-color: #0b1329 !important;
            color: #00f0ff !important;
            border-color: #00f0ff !important;
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.8) !important;
        }
        
        h1 { color: #0F172A !important; font-weight: 700; }
        h2 { color: #1E293B !important; font-weight: 600; font-size: 1.3rem !important; }
        h3 { color: #0F172A !important; font-weight: 600; font-size: 1.1rem !important; }

        .stForm label, .stTextInput label, .stSelectbox label, .stDateInput label, .stNumberInput label, div[data-testid="stForm"] label {
            color: #000000 !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
        }

        .stButton>button { 
            background-color: #7c3aed; 
            color: white; 
            border-radius: 8px; 
            font-weight: bold; 
            border: none;
        }
        .stButton>button:hover { background-color: #00FFFF; color: white; }
        [data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; border: 1px solid #E2E8F0; }
        </style>
    """, unsafe_allow_html=True)

# Helper Function for Glove Class
def get_glove_class(prod_code):
    code_str = str(prod_code)
    for num in ['075', '110']:
        if num in code_str: return 'Class 00'
    for num in ['102', '160']:
        if num in code_str: return 'Class 0'
    for num in ['152', '210']:
        if num in code_str: return 'Class 1'
    for num in ['229', '290']:
        if num in code_str: return 'Class 2'
    for num in ['292', '350']:
        if num in code_str: return 'Class 3'
    for num in ['356', '420']:
        if num in code_str: return 'Class 4'
    return 'Unclassified'

# --- 1. LOGIN MODULE ---
def login_screen():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_a, col_main, col_b = st.columns([1, 1.2, 1])
    
    with col_main:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #0f172a; margin-bottom: 25px;'>Login</h2>", unsafe_allow_html=True)
        
        username = st.text_input("Username / Email", key="login_user", placeholder="Enter your email or username")
        password = st.text_input("Password", type="password", key="login_pass", placeholder="Enter your password")
        
        col_sub1, col_sub2 = st.columns(2)
        with col_sub1:
            st.checkbox("Remember me", key="remember_me")
        with col_sub2:
            st.markdown("<p style='text-align: right; font-size: 14px; margin-top: 5px;'><a href='#' style='color: #7c3aed; text-decoration: none;'>Forgot password?</a></p>", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Login Now", use_container_width=True):
            cursor = conn.cursor()
            cursor.execute("SELECT password, role FROM users WHERE username = ?", (username,))
            user_data = cursor.fetchone()
            
            if user_data and user_data[0] == password:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['role'] = user_data[1]
                
                st.query_params["user"] = username
                st.query_params["role"] = user_data[1]
                
                st.success(f"Welcome back, {username.capitalize()}!")
                st.rerun()
            else:
                st.error("❌ Invalid Username or Password!")
        
        st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state['logged_in']:
    login_screen()
else:
    st.sidebar.markdown(f"### 👤 {st.session_state['username'].capitalize()}")
    st.sidebar.markdown(f"Role: **{st.session_state['role']}**")
    st.sidebar.markdown("---")
    
    st.sidebar.subheader("📌 Navigation")
    if 'menu_choice' not in st.session_state:
        st.session_state['menu_choice'] = "Dashboard"

    if st.sidebar.button("📊 Dashboard"): st.session_state['menu_choice'] = "Dashboard"
    if st.sidebar.button("📦 Order & Plan Mgmt"): st.session_state['menu_choice'] = "Order Management"
    if st.sidebar.button("🧪 Glove Test Entry"): st.session_state['menu_choice'] = "Test Entry"
    if st.sidebar.button("🔍 Failed Analysis"): st.session_state['menu_choice'] = "Failed Analysis"
    if st.sidebar.button("📈 Reports & Progress"): st.session_state['menu_choice'] = "Reports"
    if st.sidebar.button("📋 Monthly Shipment Report"): st.session_state['menu_choice'] = "Monthly Shipment Report"
    
    role = st.session_state['role']
    if role == "Admin":
        if st.sidebar.button("👥 User Management"): st.session_state['menu_choice'] = "User Management"

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        st.session_state['role'] = ""
        st.query_params.clear()
        st.rerun()

    choice = st.session_state['menu_choice']
    months_list = ["January 2026", "February 2026", "March 2026", "April 2026", "May 2026", "June 2026", "July 2026", "August 2026", "September 2026", "October 2026", "November 2026", "December 2026"]

    # --- 2. ORDER & MONTHLY PLAN MANAGEMENT ---
    if choice == "Order Management":
        st.header("📦 Monthly Order & Plan Management")
        st.markdown("Manage, upload, or configure quantities for production orders.")
        
        if role in ["Admin", "Supervisor"]:
            tab1, tab2, tab3 = st.tabs(["➕ Add Single Order", "📂 Upload via Excel", "⚙️ Admin Order Edit"])
            
            with tab1:
                with st.form("monthly_plan_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        selected_month = st.selectbox("Select Month & Year", months_list)
                        order_name = st.text_input("Order Name / Customer Name")
                        product_code = st.text_input("Product Code (e.g. 61C102R10OUA280S1)")
                    with col2:
                        order_no = st.text_input("Order Number")
                        order_qty = st.number_input("Order Quantity (Glove Pairs)", min_value=1, value=100)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.form_submit_button("Save Monthly Order"):
                        if order_name and order_no and product_code:
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO orders (month, order_name, order_no, product_code, target_qty) VALUES (?, ?, ?, ?, ?)",
                                           (selected_month, str(order_name), str(order_no), str(product_code), int(order_qty)))
                            conn.commit()
                            st.success("✅ Order successfully saved to Database!")
                        else:
                            st.warning("Please fill all required fields.")
            
            with tab2:
                upload_month_choice = st.selectbox("Select Month for Uploaded Orders", months_list, key="up_month_sel")
                sample_df = pd.DataFrame({
                    'Order Name': ['Customer A', 'Customer B'], 'Order No': ['ORD-001', 'ORD-002'],
                    'Product Code': ['61C075', '61C102'], 'Order Qty': [500, 1200]
                })
                output_sample = io.BytesIO()
                with pd.ExcelWriter(output_sample, engine='openpyxl') as writer:
                    sample_df.to_excel(writer, index=False, sheet_name='Template')
                st.download_button("📥 Download Sample Excel Template", data=output_sample.getvalue(), file_name="Order_Template.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
                uploaded_file = st.file_uploader("Upload Excel / CSV File", type=["xlsx", "xls", "csv"])
                if uploaded_file is not None:
                    try:
                        up_df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                        if st.button("🚀 Process & Save Uploaded Orders"):
                            qty_col_name = 'Order Qty' if 'Order Qty' in up_df.columns else ('Target Qty' if 'Target Qty' in up_df.columns else None)
                            required_cols = ['Order Name', 'Order No', 'Product Code']
                            
                            if qty_col_name and all(col in up_df.columns for col in required_cols):
                                cursor = conn.cursor()
                                for _, row in up_df.iterrows():
                                    cursor.execute("INSERT INTO orders (month, order_name, order_no, product_code, target_qty) VALUES (?, ?, ?, ?, ?)",
                                                   (upload_month_choice, str(row['Order Name']), str(row['Order No']), str(row['Product Code']), int(row[qty_col_name])))
                                conn.commit()
                                st.success("Orders imported and saved to Database successfully!")
                                st.rerun()
                            else:
                                st.error(f"Columns mismatch! Required: Order Name, Order No, Product Code, and Order Qty")
                    except Exception as e:
                        st.error(f"Error: {e}")

            with tab3:
                if role == "Admin":
                    orders_df_edit = load_orders_safe(conn)
                    if not orders_df_edit.empty:
                        sel_ord_id = st.selectbox("Select Order ID to Edit", orders_df_edit['id'].tolist())
                        curr_row = orders_df_edit[orders_df_edit['id'] == sel_ord_id].iloc[0]
                        
                        with st.form("edit_order_form"):
                            e_month = st.selectbox("Month", months_list, index=months_list.index(curr_row['month']) if curr_row['month'] in months_list else 0)
                            e_name = st.text_input("Order Name", value=str(curr_row['order_name']))
                            e_no = st.text_input("Order No", value=str(curr_row['order_no']))
                            e_code = st.text_input("Product Code", value=str(curr_row['product_code']))
                            e_order_qty = st.number_input("Order Qty", min_value=1, value=int(curr_row['target_qty']))
                            
                            if st.form_submit_button("💾 Update Order"):
                                cursor = conn.cursor()
                                cursor.execute("UPDATE orders SET month=?, order_name=?, order_no=?, product_code=?, target_qty=? WHERE id=?",
                                               (e_month, e_name, e_no, e_code, e_order_qty, sel_ord_id))
                                conn.commit()
                                st.success("Order updated successfully!")
                                st.rerun()
                    else:
                        st.info("No orders found to edit.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 Existing Orders Table")
        orders_df = load_orders_safe(conn)
        if not orders_df.empty:
            orders_display = orders_df[['month', 'order_name', 'order_no', 'product_code', 'target_qty']].copy()
            orders_display.columns = ['Month', 'Order Name', 'Order No', 'Product Code', 'Order Qty']
            filter_m = st.selectbox("Filter Orders by Month", orders_display['Month'].unique())
            st.dataframe(orders_display[orders_display['Month'] == filter_m], use_container_width=True)
        else:
            st.info("No orders found in database.")

    # --- 3. TEST ENTRY ---
    elif choice == "Test Entry":
        st.header("🧪 Electric Glove Proof Testing Entry")
        st.markdown("Record daily proof testing results for left and right hands.")
        
        orders_df = load_orders_safe(conn)
        if orders_df.empty:
            st.warning("⚠️ කරුණාකර පළමුව Order & Plan Management වෙත ගොස් Order එකක් ඇතුළත් කරන්න!")
        else:
            with st.form("test_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    test_date = st.date_input("Test Date", datetime.today())
                    available_order_months = orders_df['month'].unique().tolist()
                    sel_test_month = st.selectbox("Select Month", available_order_months)
                    
                    month_orders = orders_df[orders_df['month'] == sel_test_month]
                    
                    if not month_orders.empty:
                        order_no_sel = st.selectbox("Select Order No", month_orders['order_no'].unique())
                        available_codes = month_orders['product_code'].unique().tolist()
                        prod_code_sel = st.selectbox("Select Product Code (Type to filter)", available_codes)
                    else:
                        order_no_sel = ""
                        prod_code_sel = ""
                        st.warning("මෙම මාසයට අදාළ Orders හමුවී නැත.")
                    
                    machine_no = st.selectbox("Machine Number", ["Machine 01", "Machine 02", "Machine 03", "Machine 04", "Machine 05"])
                
                with col2:
                    l_pass = st.number_input("Left Hand Pass Qty", min_value=0, value=0)
                    r_pass = st.number_input("Right Hand Pass Qty", min_value=0, value=0)
                    l_fail = st.number_input("Left Hand Fail Qty", min_value=0, value=0)
                    r_fail = st.number_input("Right Hand Fail Qty", min_value=0, value=0)
                    remarks = st.text_input("Remarks")
                
                st.markdown("<br>", unsafe_allow_html=True)
                submit_test = st.form_submit_button("💾 Save Test Entry")
                
                if submit_test:
                    if order_no_sel and str(prod_code_sel).strip():
                        tot_l_tested = l_pass + l_fail
                        tot_r_tested = r_pass + r_fail
                        
                        entry_tested_pairs = float(min(tot_l_tested, tot_r_tested))
                        entry_pass_pairs = float(min(l_pass, r_pass)) if (l_pass > 0 and r_pass > 0) else float(l_pass + r_pass)
                        total_fail = l_fail + r_fail
                        
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO test_entries (date, month, order_no, product_code, machine_number, left_pass, right_pass, left_fail, right_fail, tested_pairs, pass_pairs, total_fail, logged_user, remarks)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (str(test_date), sel_test_month, order_no_sel, str(prod_code_sel).strip(), machine_no, l_pass, r_pass, l_fail, r_fail, entry_tested_pairs, entry_pass_pairs, int(total_fail), st.session_state['username'], remarks))
                        conn.commit()
                        st.success(f"✅ Test successfully saved to Database!")
                        st.rerun()
                    else:
                        st.error("❌ කරුණාකර Order No සහ Product Code එක නිවැරදිව ලබා දෙන්න.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 Test Entries History")
        
        tests_df = pd.read_sql("""
            SELECT rowid as id, date as Date, month as Month, order_no as 'Order No', 
                   product_code as 'Product Code', machine_number as 'Machine', 
                   left_pass as 'Left Pass', left_fail as 'Left Fail', 
                   right_pass as 'Right Pass', right_fail as 'Right Fail', 
                   tested_pairs as 'Tested Pairs', pass_pairs as 'Pass Pairs', 
                   total_fail as 'Total Fail', logged_user as 'Logged User', remarks as Remarks 
            FROM test_entries
        """, conn)
        
        if not tests_df.empty:
            tests_df.insert(0, 'No.', range(1, len(tests_df) + 1))
            display_df = tests_df.drop(columns=['id'])
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("No test records yet.")

    # --- 4. FAILED ANALYSIS ---
    elif choice == "Failed Analysis":
        st.header("🔍 Daily Failed Analysis by Full Product Code (Including S/B)")
        st.markdown("Select a specific Month and Date to view exact product code failure details.")
        
        try:
            query = """
                SELECT date, month, product_code, left_fail, right_fail, total_fail 
                FROM test_entries 
                WHERE (left_fail > 0 OR right_fail > 0 OR total_fail > 0)
            """
            tests_df_check = pd.read_sql(query, conn)
            
            if not tests_df_check.empty:
                date_col = 'date'
                month_col = 'month'
                
                available_months = sorted(tests_df_check[month_col].dropna().unique().tolist())
                if available_months:
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        sel_month = st.selectbox("📅 Select Month", available_months)
                    
                    filtered_by_month = tests_df_check[tests_df_check[month_col] == sel_month]
                    available_dates = sorted(filtered_by_month[date_col].dropna().unique().tolist())
                    
                    with col_f2:
                        sel_date = st.selectbox("📆 Select Date", available_dates) if available_dates else None
                    
                    final_filtered_df = filtered_by_month[filtered_by_month[date_col] == sel_date] if sel_date else filtered_by_month
                else:
                    final_filtered_df = tests_df_check

                if not final_filtered_df.empty:
                    final_filtered_df['Exact_Product_Code'] = final_filtered_df['product_code'].astype(str).str.strip().str.upper()
                    
                    df_grouped = final_filtered_df.groupby(['Exact_Product_Code', date_col]).agg({
                        'left_fail': 'sum',
                        'right_fail': 'sum',
                        'total_fail': 'sum'
                    }).reset_index()
                    
                    df_grouped['Equivalent_Fail_Pairs'] = (df_grouped['left_fail'] + df_grouped['right_fail']) / 2.0
                    df_grouped = df_grouped[df_grouped['Equivalent_Fail_Pairs'] > 0]

                    st.markdown(f"### Exact Product Code Defect Summary for Date: {sel_date if 'sel_date' in locals() else 'All'}")
                    
                    if not df_grouped.empty:
                        display_fail_df = df_grouped[['Exact_Product_Code', date_col, 'left_fail', 'right_fail', 'Equivalent_Fail_Pairs']]
                        display_fail_df.columns = ['Product Code', 'Date', 'Left Fails', 'Right Fails', 'Equivalent Fail Pairs']
                        
                        st.dataframe(display_fail_df, use_container_width=True)
                        
                        st.markdown("### Failure Trend Chart")
                        pivot_chart = display_fail_df.pivot(index='Date', columns='Product Code', values='Equivalent Fail Pairs').fillna(0)
                        st.bar_chart(pivot_chart)
                    else:
                        st.info("✨ No actual failures recorded for the selected date.")
                else:
                    st.info("✨ No failure records found for the selected Month and Date.")
            else:
                st.info("✨ No failure records available in the database at all.")
        except Exception as e:
            st.warning(f"Error processing product codes: {e}")

    # --- 5. MONTHLY SHIPMENT REPORT (NEW TAB) ---
    elif choice == "Monthly Shipment Report":
        st.header("📋 Monthly Shipment Report")
        st.markdown("View summary and details of orders, pass quantities, and remaining quantities for a specific month and order name.")
        
        orders_df = load_orders_safe(conn)
        tests_df = pd.read_sql("SELECT * FROM test_entries", conn)
        
        if not orders_df.empty:
            # 1. Month and Year Selection
            available_report_months = sorted(orders_df['month'].unique().tolist())
            sel_rep_month = st.selectbox("Month and Year", available_report_months)
            
            month_orders_full = orders_df[orders_df['month'] == sel_rep_month]
            
            if not month_orders_full.empty:
                # 2. Order Name Selection
                available_order_names = sorted(month_orders_full['order_name'].unique().tolist())
                sel_rep_order_name = st.selectbox("Order Name", available_order_names)
                
                # Filter orders matching selected month and order name
                selected_orders = month_orders_full[month_orders_full['order_name'] == sel_rep_order_name]
                
                # Aggregate total targets for this order name
                total_order_qty = int(selected_orders['target_qty'].astype(int).sum())
                
                # Calculate total passed pairs from test entries for these orders
                total_pass_qty = 0
                table_rows = []
                
                for _, ord_row in selected_orders.iterrows():
                    o_no = ord_row['order_no']
                    p_code = ord_row['product_code']
                    o_target = int(ord_row['target_qty'])
                    
                    # Get passes for this order number and product code
                    match_tests = pd.DataFrame()
                    if not tests_df.empty:
                        match_tests = tests_df[(tests_df['month'] == sel_rep_month) & 
                                               (tests_df['order_no'].astype(str) == str(o_no)) & 
                                               (tests_df['product_code'].astype(str).str.strip() == str(p_code).strip())]
                    
                    o_pass_qty = int(match_tests['pass_pairs'].astype(float).sum()) if not match_tests.empty else 0
                    total_pass_qty += o_pass_qty
                    o_remaining = max(0, o_target - o_pass_qty)
                    
                    table_rows.append({
                        'Order number': o_no,
                        'Product code': p_code,
                        'Order Qty': o_target,
                        'Pass Qty': o_pass_qty,
                        'Remaining Qty': o_remaining
                    })
                
                total_remaining_qty = max(0, total_order_qty - total_pass_qty)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Display Summary Metrics boxes as sketched
                m_col1, m_col2, m_col3 = st.columns(3)
                with m_col1:
                    st.metric("Order Qty", total_order_qty)
                with m_col2:
                    st.metric("Pass Qty", total_pass_qty)
                with m_col3:
                    st.metric("Remaining Qty", total_remaining_qty)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader(f"Detailed Shipment Breakdown for: {sel_rep_order_name}")
                
                if table_rows:
                    rep_table_df = pd.DataFrame(table_rows)
                    st.dataframe(rep_table_df, use_container_width=True)
                    
                    # Export button for the shipment report
                    try:
                        output_rep = io.BytesIO()
                        with pd.ExcelWriter(output_rep, engine='openpyxl') as writer:
                            rep_table_df.to_excel(writer, index=False, sheet_name='Shipment_Report')
                        st.download_button(
                            label="📥 Download Shipment Report as Excel",
                            data=output_rep.getvalue(),
                            file_name=f"Shipment_Report_{sel_rep_month.replace(' ', '_')}_{sel_rep_order_name.replace(' ', '_')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except Exception:
                        pass
                else:
                    st.info("No detailed items found for this order name.")
            else:
                st.warning("No orders found for the selected month.")
        else:
            st.info("No orders available in the database to generate shipment reports.")

    # --- 6. USER MANAGEMENT ---
    elif choice == "User Management" and role == "Admin":
        st.header("👥 Operator & User Management")
        with st.form("add_user_form"):
            nu = st.text_input("New Username")
            np = st.text_input("Password", type="password")
            nr = st.selectbox("Role", ["Operator", "Supervisor", "Admin"])
            if st.form_submit_button("Add User"):
                if nu and np:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (nu, np, nr))
                        conn.commit()
                        st.success("User added successfully!")
                    except sqlite3.IntegrityError:
                        st.error("Username already exists!")
                else:
                    st.warning("Fill all fields.")
        
        users_df = pd.read_sql("SELECT username as Username, role as Role FROM users", conn)
        st.dataframe(users_df, use_container_width=True)

    # --- 7. DASHBOARD ---
    elif choice == "Dashboard":
        st.header("📊 Electric Glove Testing Dashboard")
        st.markdown("Overview of order quantities, pass quantities, and testing performance.")
        
        orders_df = load_orders_safe(conn)
        tests_df = pd.read_sql("SELECT * FROM test_entries", conn)
        
        if not orders_df.empty or not tests_df.empty:
            all_db_months = sorted(list(set(orders_df['month'].tolist() if not orders_df.empty else [] + 
                                            tests_df['month'].tolist() if not tests_df.empty else [])))
            available_months = all_db_months if all_db_months else months_list
            
            dash_col1, dash_col2 = st.columns([2, 4])
            with dash_col1:
                selected_dash_month = st.selectbox("📅 Select Month & Year for Dashboard", available_months, key="dash_month_sel")
            
            f_orders = orders_df[orders_df['month'] == selected_dash_month] if not orders_df.empty else pd.DataFrame()
            f_tests = tests_df[tests_df['month'] == selected_dash_month] if not tests_df.empty else pd.DataFrame()
            
            st.markdown(f"### 📋 Summary for: **{selected_dash_month}**")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📦 Total Orders", len(f_orders))
            col2.metric("🎯 Order Qty (Pairs)", int(f_orders['target_qty'].astype(int).sum()) if not f_orders.empty and 'target_qty' in f_orders.columns else 0)
            col3.metric("✅ Tested Pass Qty", int(f_tests['pass_pairs'].astype(float).sum()) if not f_tests.empty else 0)
            col4.metric("❌ Total Defective", int(f_tests['total_fail'].astype(int).sum()) if not f_tests.empty else 0)
            
            st.markdown("---")
            
            if not f_tests.empty:
                st.subheader(f"📈 Daily Testing Performance - {selected_dash_month}")
                daily_chart_df = f_tests.groupby('date')[['pass_pairs', 'total_fail']].sum()
                st.bar_chart(daily_chart_df)
                
                st.subheader(f"🛡️ Class-wise Breakdown - {selected_dash_month}")
                f_tests['Glove Class'] = f_tests['product_code'].apply(get_glove_class)
                
                class_summary_list = []
                for g_class, g_df in f_tests.groupby('Glove Class'):
                    sum_lp = g_df['left_pass'].sum()
                    sum_rp = g_df['right_pass'].sum()
                    sum_lf = g_df['left_fail'].sum()
                    sum_rf = g_df['right_fail'].sum()
                    
                    c_tested_pairs = (sum_lp + sum_rp + sum_lf + sum_rf) / 2.0
                    c_pass_pairs = (sum_lp + sum_rp) / 2.0
                    c_total_fail = (sum_lf + sum_rf) / 2.0
                    c_fail_pct = round((c_total_fail / c_tested_pairs * 100), 2) if c_tested_pairs > 0 else 0.0
                    
                    class_summary_list.append({
                        'Glove Class': g_class,
                        'Tested Pairs': c_tested_pairs,
                        'Pass Pairs': c_pass_pairs,
                        'Total Fail': c_total_fail,
                        'Fail %': c_fail_pct
                    })
                
                class_summary_df = pd.DataFrame(class_summary_list)[['Glove Class', 'Tested Pairs', 'Pass Pairs', 'Total Fail', 'Fail %']]
                st.dataframe(class_summary_df, use_container_width=True)
            else:
                st.info(f"ℹ️ No test records found for {selected_dash_month}.")
        else:
            st.info("No data available in the system yet.")

    # --- 8. REPORTS & PROGRESS ---
    elif choice == "Reports":
        st.header("📈 Monthly Reports & Class-wise Breakdown")
        st.markdown("Detailed order progression, daily/monthly class summaries, and export tools.")
        
        orders_df = load_orders_safe(conn)
        tests_df = pd.read_sql("SELECT * FROM test_entries", conn)
        
        if not orders_df.empty or not tests_df.empty:
            all_months = sorted(list(set(orders_df['month'].tolist() + tests_df['month'].tolist()))) if not orders_df.empty else tests_df['month'].unique()
            report_month = st.selectbox("Select Month for Report", all_months)
            
            m_orders = orders_df[orders_df['month'] == report_month] if not orders_df.empty else pd.DataFrame()
            m_tests = tests_df[tests_df['month'] == report_month] if not tests_df.empty else pd.DataFrame()
            
            st.subheader("🗓️ Order Progress Summary")
            summary_list = []
            
            if not m_tests.empty:
                grouped_tests = m_tests.groupby(['order_no', 'product_code']).agg({
                    'left_pass': 'sum', 'right_pass': 'sum',
                    'left_fail': 'sum', 'right_fail': 'sum'
                }).reset_index()
                
                for _, t_row in grouped_tests.iterrows():
                    ord_no = t_row['order_no']
                    prod_code = t_row['product_code']
                    
                    matched_order = m_orders[(m_orders['order_no'] == ord_no) & (m_orders['product_code'] == prod_code)]
                    
                    if not matched_order.empty:
                        order_name = matched_order.iloc[0]['order_name']
                        order_qty = int(matched_order.iloc[0]['target_qty'])
                    else:
                        order_name = "Unknown / Direct"
                        order_qty = 0
                    
                    tot_lp = int(t_row['left_pass'])
                    tot_rp = int(t_row['right_pass'])
                    tot_lf = int(t_row['left_fail'])
                    tot_rf = int(t_row['right_fail'])
                    
                    tot_l_tested = tot_lp + tot_lf
                    tot_r_tested = tot_rp + tot_rf
                    
                    tested_pairs = min(tot_l_tested, tot_r_tested)
                    pass_pairs = min(tot_lp, tot_rp) if (tot_lp > 0 and tot_rp > 0) else 0
                    
                    single_left_remain = max(0, tot_l_tested - tested_pairs)
                    single_right_remain = max(0, tot_r_tested - tested_pairs)
                    
                    if (tot_l_tested == 0) and (tot_r_tested == 0):
                        continue
                        
                    remaining_qty = max(0, order_qty - pass_pairs) if order_qty > 0 else 0
                    
                    summary_list.append({
                        'Order No': ord_no, 'Product Code': prod_code, 'Glove Class': get_glove_class(prod_code),
                        'Order Name': order_name, 'Order Qty': order_qty, 
                        'Tested Pairs': tested_pairs, 'Pass Pairs': pass_pairs, 
                        'Single Left (Extra)': single_left_remain, 'Single Right (Extra)': single_right_remain,
                        'Pass Left': tot_lp, 'Pass Right': tot_rp, 
                        'Fail Left': tot_lf, 'Fail Right': tot_rf, 
                        'Remaining Qty': remaining_qty
                    })
            
            if summary_list:
                summary_df = pd.DataFrame(summary_list)
                
                def highlight_completed(row_data):
                    if row_data['Order Qty'] > 0 and row_data['Pass Pairs'] >= row_data['Order Qty']:
                        return ['background-color: #D4EDDA'] * len(row_data)
                    return [''] * len(row_data)
                
                styled_summary_df = summary_df.style.apply(highlight_completed, axis=1)
                st.dataframe(styled_summary_df, use_container_width=True)
            else:
                st.info("No active test orders found for this month.")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("🛡️ Class-wise Testing Summary")
            if not m_tests.empty:
                m_tests['Glove Class'] = m_tests['product_code'].apply(get_glove_class)
                
                available_dates = sorted(m_tests['date'].unique())
                selected_date = st.selectbox("Select Date to View Daily Class Qty", available_dates)
                
                daily_tests = m_tests[m_tests['date'] == selected_date]
                
                daily_summary_list = []
                for g_class, g_df in daily_tests.groupby('Glove Class'):
                    sum_lp = g_df['left_pass'].sum()
                    sum_rp = g_df['right_pass'].sum()
                    sum_lf = g_df['left_fail'].sum()
                    sum_rf = g_df['right_fail'].sum()
                    
                    d_tested_pairs = (sum_lp + sum_rp + sum_lf + sum_rf) / 2.0
                    d_pass_pairs = (sum_lp + sum_rp) / 2.0
                    d_total_fail = (sum_lf + sum_rf) / 2.0
                    d_fail_pct = round((d_total_fail / d_tested_pairs * 100), 2) if d_tested_pairs > 0 else 0.0
                    
                    daily_summary_list.append({
                        'Glove Class': g_class, 'Tested Pairs': d_tested_pairs,
                        'Pass Pairs': d_pass_pairs, 'Total Fail': d_total_fail, 'Fail %': d_fail_pct
                    })
                
                st.markdown(f"**📅 Date: {selected_date}**")
                daily_summary_df = pd.DataFrame(daily_summary_list)[['Glove Class', 'Tested Pairs', 'Pass Pairs', 'Total Fail', 'Fail %']]
                st.dataframe(daily_summary_df, use_container_width=True)
                
                st.markdown("**📊 Monthly Total Class-wise Summary**")
                monthly_summary_list = []
                for g_class, g_df in m_tests.groupby('Glove Class'):
                    sum_lp = g_df['left_pass'].sum()
                    sum_rp = g_df['right_pass'].sum()
                    sum_lf = g_df['left_fail'].sum()
                    sum_rf = g_df['right_fail'].sum()
                    
                    m_tested_pairs = (sum_lp + sum_rp + sum_lf + sum_rf) / 2.0
                    m_pass_pairs = (sum_lp + sum_rp) / 2.0
                    m_total_fail = (sum_lf + sum_rf) / 2.0
                    m_fail_pct = round((m_total_fail / m_tested_pairs * 100), 2) if m_tested_pairs > 0 else 0.0
                    
                    monthly_summary_list.append({
                        'Glove Class': g_class, 'Tested Pairs': m_tested_pairs,
                        'Pass Pairs': m_pass_pairs, 'Total Fail': m_total_fail, 'Fail %': m_fail_pct
                    })
                
                monthly_summary_df = pd.DataFrame(monthly_summary_list)[['Glove Class', 'Tested Pairs', 'Pass Pairs', 'Total Fail', 'Fail %']]
                st.dataframe(monthly_summary_df, use_container_width=True)
            else:
                st.info("No test records found for this month.")

            st.markdown("<br>", unsafe_allow_html=True)
            try:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    if summary_list:
                        pd.DataFrame(summary_list).to_excel(writer, index=False, sheet_name='Order_Progress')
                    if not m_tests.empty:
                        m_tests.to_excel(writer, index=False, sheet_name='Test_History')
                
                st.download_button(
                    label=f"📥 Download {report_month} Complete Report as Excel",
                    data=output.getvalue(),
                    file_name=f"Glove_Report_{report_month.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                pass
        else:
            st.info("No data available.")