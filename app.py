import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Page Configuration
st.set_page_config(page_title="Electric Glove Proof Testing System", layout="wide")

# --- CUSTOM CSS FOR BLUE, WHITE & LIGHT BLUE THEME & BACKGROUND ---
st.markdown("""
    <style>
    .stApp {
        background-color: #F0F8FF;
    }
    [data-testid="stSidebar"] {
        background-color: #E6F2FF;
        border-right: 2px solid #B0E0E6;
    }
    h1, h2, h3 {
        color: #003366 !important;
    }
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

# Initialize Session State
if 'users' not in st.session_state:
    st.session_state['users'] = {
        "admin": {"password": "123", "role": "Admin"},
        "supervisor": {"password": "123", "role": "Supervisor"},
        "operator": {"password": "123", "role": "Operator"}
    }

if 'orders' not in st.session_state:
    st.session_state['orders'] = pd.DataFrame(columns=[
        'Month', 'Order Name', 'Order No', 'Product Code', 'Target Qty'
    ])

if 'test_entries' not in st.session_state:
    st.session_state['test_entries'] = pd.DataFrame(columns=[
        'Date', 'Month', 'Order No', 'Product Code', 'Machine Number', 
        'Left Pass', 'Right Pass', 'Left Fail', 'Right Fail', 
        'Tested Pairs', 'Pass Pairs', 'Total Fail', 'Logged User', 'Remarks'
    ])

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['role'] = ""

# Helper Function to Determine Glove Class based on Product Code numbers
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
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.title("⚡ Electric Glove Proof Testing System")
    st.markdown("### Secure Login Portal")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username")
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
    st.sidebar.title(f"👤 User: {st.session_state['username'].capitalize()}")
    st.sidebar.write(f"Role: **{st.session_state['role']}**")
    st.sidebar.markdown("---")
    
    st.sidebar.subheader("📌 Navigation Menu")
    if 'menu_choice' not in st.session_state:
        st.session_state['menu_choice'] = "Dashboard"

    if st.sidebar.button("📊 Dashboard", use_container_width=True): st.session_state['menu_choice'] = "Dashboard"
    if st.sidebar.button("📦 Order & Plan Mgmt", use_container_width=True): st.session_state['menu_choice'] = "Order Management"
    if st.sidebar.button("🧪 Glove Test Entry", use_container_width=True): st.session_state['menu_choice'] = "Test Entry"
    if st.sidebar.button("📈 Reports & Progress", use_container_width=True): st.session_state['menu_choice'] = "Reports"
    
    role = st.session_state['role']
    if role == "Admin":
        if st.sidebar.button("👥 User Management", use_container_width=True): st.session_state['menu_choice'] = "User Management"

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

    choice = st.session_state['menu_choice']
    months_list = ["January 2026", "February 2026", "March 2026", "April 2026", "May 2026", "June 2026", "July 2026", "August 2026", "September 2026", "October 2026", "November 2026", "December 2026"]

    # --- 2. ORDER & MONTHLY PLAN MANAGEMENT ---
    if choice == "Order Management":
        st.header("📦 Monthly Order & Plan Management")
        
        if role in ["Admin", "Supervisor"]:
            tab1, tab2, tab3 = st.tabs(["➕ Add Single Order", "📂 Upload Orders via Excel", "⚙️ Admin Order Edit / Update"])
            
            with tab1:
                with st.form("monthly_plan_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        selected_month = st.selectbox("Select Month & Year", months_list)
                        order_name = st.text_input("Order Name / Customer Name")
                        product_code = st.text_input("Product Code (e.g. 61c075)")
                    with col2:
                        order_no = st.text_input("Order Number")
                        target_qty = st.number_input("Target Quantity (Glove Pairs)", min_value=1, value=100)
                    
                    if st.form_submit_button("Save Monthly Order"):
                        if order_name and order_no and product_code:
                            new_row = pd.DataFrame({
                                'Month': [selected_month], 'Order Name': [str(order_name)],
                                'Order No': [str(order_no)], 'Product Code': [str(product_code)],
                                'Target Qty': [int(target_qty)]
                            })
                            st.session_state['orders'] = pd.concat([st.session_state['orders'], new_row], ignore_index=True)
                            st.success("Order added successfully!")
                        else:
                            st.warning("Please fill all required fields.")
            
            with tab2:
                upload_month_choice = st.selectbox("Select Month for Uploaded Orders", months_list, key="up_month_sel")
                sample_df = pd.DataFrame({
                    'Order Name': ['Customer A', 'Customer B'], 'Order No': ['ORD-001', 'ORD-002'],
                    'Product Code': ['61c075', '61c102'], 'Target Qty': [500, 1200]
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
                            required_cols = ['Order Name', 'Order No', 'Product Code', 'Target Qty']
                            if all(col in up_df.columns for col in required_cols):
                                up_df['Month'] = upload_month_choice
                                up_df['Target Qty'] = up_df['Target Qty'].astype(int)
                                st.session_state['orders'] = pd.concat([st.session_state['orders'], up_df], ignore_index=True)
                                st.success("Orders imported successfully!")
                                st.rerun()
                            else:
                                st.error(f"Columns mismatch! Required: {required_cols}")
                    except Exception as e:
                        st.error(f"Error: {e}")

            with tab3:
                if role == "Admin":
                    st.info("Admin Facility: Edit or Update existing orders.")
                    if not st.session_state['orders'].empty:
                        order_indices = st.session_state['orders'].index.tolist()
                        sel_ord_idx = st.selectbox("Select Order Index to Edit", order_indices)
                        
                        curr_row = st.session_state['orders'].loc[sel_ord_idx]
                        with st.form("edit_order_form"):
                            e_month = st.selectbox("Month", months_list, index=months_list.index(curr_row['Month']) if curr_row['Month'] in months_list else 0)
                            e_name = st.text_input("Order Name", value=curr_row['Order Name'])
                            e_no = st.text_input("Order No", value=curr_row['Order No'])
                            e_code = st.text_input("Product Code", value=curr_row['Product Code'])
                            e_target = st.number_input("Target Qty", min_value=1, value=int(curr_row['Target Qty']))
                            
                            if st.form_submit_button("💾 Update Order"):
                                st.session_state['orders'].loc[sel_ord_idx] = [e_month, e_name, e_no, e_code, e_target]
                                st.success("Order updated successfully!")
                                st.rerun()
                    else:
                        st.info("No orders found to edit.")
                else:
                    st.warning("Order editing is restricted to Admin users only.")
        
        st.subheader("📋 Existing Orders List")
        if not st.session_state['orders'].empty:
            filter_m = st.selectbox("Filter Orders by Month", st.session_state['orders']['Month'].unique())
            st.dataframe(st.session_state['orders'][st.session_state['orders']['Month'] == filter_m], use_container_width=True)
            if role == "Admin" and st.button("Clear All Orders Data"):
                st.session_state['orders'] = pd.DataFrame(columns=st.session_state['orders'].columns)
                st.rerun()
        else:
            st.info("No orders found.")

    # --- 3. TEST ENTRY ---
    elif choice == "Test Entry":
        st.header("🧪 Electric Glove Proof Testing Entry")
        
        orders_df = st.session_state['orders']
        if orders_df.empty:
            st.warning("Please add orders first!")
        else:
            with st.form("test_form"):
                col1, col2 = st.columns(2)
                with col1:
                    test_date = st.date_input("Test Date", datetime.today())
                    sel_test_month = st.selectbox("Select Month", orders_df['Month'].unique())
                    month_orders = orders_df[orders_df['Month'] == sel_test_month]
                    
                    if not month_orders.empty:
                        order_no_sel = st.selectbox("Select Order No", month_orders['Order No'].unique())
                        filtered_codes = month_orders[month_orders['Order No'] == order_no_sel]['Product Code'].unique()
                        prod_code_sel = st.selectbox("Select Product Code", filtered_codes)
                        
                        detected_class = get_glove_class(prod_code_sel)
                        st.info(f"Detected Glove Class: **{detected_class}**")
                    else:
                        order_no_sel, prod_code_sel = "", ""
                    
                    machine_no = st.selectbox("Machine Number", ["Machine 01", "Machine 02", "Machine 03", "Machine 04", "Machine 05"])
                
                with col2:
                    l_pass = st.number_input("Left Hand Pass Qty", min_value=0, value=0)
                    r_pass = st.number_input("Right Hand Pass Qty", min_value=0, value=0)
                    l_fail = st.number_input("Left Hand Fail Qty", min_value=0, value=0)
                    r_fail = st.number_input("Right Hand Fail Qty", min_value=0, value=0)
                    remarks = st.text_input("Remarks")
                
                if st.form_submit_button("Save Test Entry"):
                    if order_no_sel and prod_code_sel:
                        tested_pairs = max(l_pass + l_fail, r_pass + r_fail)
                        full_pairs = min(l_pass, r_pass)
                        rem_left = l_pass - full_pairs
                        rem_right = r_pass - full_pairs
                        pass_pairs_val = full_pairs + (0.5 if (rem_left > 0 or rem_right > 0) else 0.0)
                        
                        total_fail = l_fail + r_fail
                        
                        new_test = pd.DataFrame({
                            'Date': [str(test_date)], 'Month': [sel_test_month],
                            'Order No': [order_no_sel], 'Product Code': [prod_code_sel],
                            'Machine Number': [machine_no], 'Left Pass': [l_pass], 'Right Pass': [r_pass],
                            'Left Fail': [l_fail], 'Right Fail': [r_fail],
                            'Tested Pairs': [tested_pairs], 'Pass Pairs': [pass_pairs_val], 'Total Fail': [total_fail],
                            'Logged User': [st.session_state['username']], 'Remarks': [remarks]
                        })
                        st.session_state['test_entries'] = pd.concat([st.session_state['test_entries'], new_test], ignore_index=True)
                        st.success(f"Test saved! Tested Pairs: {tested_pairs}, Pass Pairs: {pass_pairs_val}")
                    else:
                        st.error("Select valid Order and Product Code.")

        st.subheader("📋 Test Entries & Management")
        tests_df = st.session_state['test_entries']
        if not tests_df.empty:
            st.dataframe(tests_df, use_container_width=True)
            if role == "Admin":
                with st.form("delete_entry_form"):
                    sel_del = st.selectbox("Select Entry Index to Delete", tests_df.index.tolist())
                    if st.form_submit_button("🗑️ Delete Entry (Admin Only)"):
                        st.session_state['test_entries'] = tests_df.drop(sel_del).reset_index(drop=True)
                        st.success("Entry deleted!")
                        st.rerun()
        else:
            st.info("No test records yet.")

    # --- 4. USER MANAGEMENT ---
    elif choice == "User Management" and role == "Admin":
        st.header("👥 Operator & User Management")
        with st.form("add_user_form"):
            nu = st.text_input("New Username")
            np = st.text_input("Password", type="password")
            nr = st.selectbox("Role", ["Operator", "Supervisor", "Admin"])
            if st.form_submit_button("Add User"):
                if nu and np:
                    st.session_state['users'][nu] = {"password": np, "role": nr}
                    st.success("User added!")
                else:
                    st.warning("Fill all fields.")
        
        users_df = pd.DataFrame([{"Username": k, "Role": v["role"]} for k, v in st.session_state['users'].items()])
        st.dataframe(users_df, use_container_width=True)

    # --- 5. DASHBOARD ---
    elif choice == "Dashboard":
        st.header("📊 Electric Glove Testing Dashboard")
        orders_df, tests_df = st.session_state['orders'], st.session_state['test_entries']
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Orders", len(orders_df))
        col2.metric("Target Qty", orders_df['Target Qty'].astype(int).sum() if not orders_df.empty else 0)
        col3.metric("Tested Pass Qty", int(tests_df['Pass Pairs'].astype(float).sum()) if not tests_df.empty else 0)
        col4.metric("Total Defective Fails", tests_df['Total Fail'].astype(int).sum() if not tests_df.empty else 0)
        
        if not tests_df.empty:
            st.bar_chart(tests_df.groupby('Month')[['Pass Pairs', 'Total Fail']].sum())

    # --- 6. REPORTS & PROGRESS ---
    elif choice == "Reports":
        st.header("📈 Monthly Reports & Class-wise Breakdown")
        
        orders_df, tests_df = st.session_state['orders'], st.session_state['test_entries']
        if not orders_df.empty or not tests_df.empty:
            all_months = sorted(list(set(orders_df['Month'].tolist() + tests_df['Month'].tolist()))) if not orders_df.empty else tests_df['Month'].unique()
            report_month = st.selectbox("Select Month for Report", all_months)
            
            m_orders = orders_df[orders_df['Month'] == report_month] if not orders_df.empty else pd.DataFrame()
            m_tests = tests_df[tests_df['Month'] == report_month] if not tests_df.empty else pd.DataFrame()
            
            # --- 1. Order Progress Table ---
            st.subheader("🗓️ Order Progress")
            summary_list = []
            
            if not m_tests.empty:
                grouped_tests = m_tests.groupby(['Order No', 'Product Code']).agg({
                    'Left Pass': 'sum',
                    'Right Pass': 'sum',
                    'Left Fail': 'sum',
                    'Right Fail': 'sum'
                }).reset_index()
                
                for _, t_row in grouped_tests.iterrows():
                    ord_no = t_row['Order No']
                    prod_code = t_row['Product Code']
                    
                    matched_order = m_orders[(m_orders['Order No'] == ord_no) & (m_orders['Product Code'] == prod_code)]
                    
                    if not matched_order.empty:
                        order_name = matched_order.iloc[0]['Order Name']
                        target = int(matched_order.iloc[0]['Target Qty'])
                    else:
                        order_name = "Unknown / Direct"
                        target = 0
                    
                    lp = int(t_row['Left Pass'])
                    rp = int(t_row['Right Pass'])
                    lf = int(t_row['Left Fail'])
                    rf = int(t_row['Right Fail'])
                    
                    tested_pairs = max(lp + lf, rp + rf)
                    full_pairs = min(lp, rp)
                    rem_l = lp - full_pairs
                    rem_r = rp - full_pairs
                    pass_pairs = full_pairs + (0.5 if (rem_l > 0 or rem_r > 0) else 0.0)
                    
                    if tested_pairs == 0:
                        continue
                        
                    remaining_qty = max(0, target - pass_pairs) if target > 0 else 0
                    
                    summary_list.append({
                        'Order No': ord_no, 'Product Code': prod_code, 'Glove Class': get_glove_class(prod_code),
                        'Order Name': order_name, 'Target Qty': target, 
                        'Tested Pairs': tested_pairs, 'Pass Pairs': pass_pairs, 
                        'Pass Left Hand': lp, 'Pass Right Hand': rp, 
                        'Fail Left Hand': lf, 'Fail Right Hand': rf, 
                        'Remaining Qty to Test': remaining_qty
                    })
            
            if summary_list:
                summary_df = pd.DataFrame(summary_list)
                
                # දශම ස්ථාන අනවශ්‍ය ලෙස දිස්වීම වැළැක්වීම (50.0 -> 50)
                summary_df['Pass Pairs'] = summary_df['Pass Pairs'].apply(lambda x: int(x) if x % 1 == 0 else round(x, 1))
                summary_df['Remaining Qty to Test'] = summary_df['Remaining Qty to Test'].apply(lambda x: int(x) if x % 1 == 0 else round(x, 1))
                
                def highlight_completed(row_data):
                    if row_data['Target Qty'] > 0 and row_data['Pass Pairs'] >= row_data['Target Qty']:
                        return ['background-color: #D4EDDA'] * len(row_data)
                    return [''] * len(row_data)
                
                styled_summary_df = summary_df.style.apply(highlight_completed, axis=1)
                st.dataframe(styled_summary_df, use_container_width=True)
            else:
                st.info("No active test orders found for this month.")
            
            # --- 2. Class-wise Testing Summary ---
            st.subheader("🛡️ Class-wise Testing Summary (Daily & Total)")
            if not m_tests.empty:
                m_tests['Glove Class'] = m_tests['Product Code'].apply(get_glove_class)
                
                available_dates = sorted(m_tests['Date'].unique())
                selected_date = st.selectbox("Select Date to View Daily Class Qty", available_dates)
                
                daily_tests = m_tests[m_tests['Date'] == selected_date]
                
                daily_class_summary = daily_tests.groupby('Glove Class').agg({
                    'Pass Pairs': 'sum',
                    'Total Fail': 'sum'
                }).reset_index()
                daily_class_summary['Tested Total'] = daily_class_summary['Pass Pairs'] + daily_class_summary['Total Fail']
                daily_class_summary['Fail %'] = daily_class_summary.apply(lambda r: round((r['Total Fail'] / r['Tested Total'] * 100), 2) if r['Tested Total'] > 0 else 0.0, axis=1)
                
                st.markdown(f"**📅 Date: {selected_date} - Class-wise Test Qty**")
                st.dataframe(daily_class_summary, use_container_width=True)
                
                st.markdown("**📊 Monthly Total Class-wise Summary**")
                monthly_class_summary = m_tests.groupby('Glove Class').agg({
                    'Pass Pairs': 'sum',
                    'Total Fail': 'sum'
                }).reset_index()
                monthly_class_summary['Tested Total'] = monthly_class_summary['Pass Pairs'] + monthly_class_summary['Total Fail']
                monthly_class_summary['Fail %'] = monthly_class_summary.apply(lambda r: round((r['Total Fail'] / r['Tested Total'] * 100), 2) if r['Tested Total'] > 0 else 0.0, axis=1)
                st.dataframe(monthly_class_summary, use_container_width=True)
            else:
                st.info("No test records found for this month.")

            # --- 3. Test Records History ---
            st.subheader("📋 Complete Test Records History")
            if not m_tests.empty:
                st.dataframe(m_tests, use_container_width=True)
            else:
                st.info("No test history available.")
                
            # Excel Download Button with Safe Error Handling
            try:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    if summary_list:
                        pd.DataFrame(summary_list).to_excel(writer, index=False, sheet_name='Order_Progress')
                    if not m_tests.empty:
                        m_tests.groupby('Glove Class').agg({'Pass Pairs': 'sum', 'Total Fail': 'sum'}).reset_index().to_excel(writer, index=False, sheet_name='Class_Summary')
                        m_tests.to_excel(writer, index=False, sheet_name='Test_History')
                
                st.download_button(
                    label=f"📥 Download {report_month} Complete Report as Excel",
                    data=output.getvalue(),
                    file_name=f"Glove_Report_{report_month.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.info("Excel download is ready once sufficient data is populated.")
        else:
            st.info("No data available.")