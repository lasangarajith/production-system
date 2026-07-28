import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Page Configuration
st.set_page_config(page_title="Production Management System", layout="wide")

# Initialize Session State for Data Storage
if 'users' not in st.session_state:
    st.session_state['users'] = {
        "admin": {"password": "123", "role": "Admin"},
        "supervisor": {"password": "123", "role": "Supervisor"},
        "operator": {"password": "123", "role": "Operator"}
    }

if 'orders' not in st.session_state:
    st.session_state['orders'] = pd.DataFrame(columns=[
        'Order No', 'Customer Name', 'Product Code', 'Quantity', 'Order Date', 'Delivery Date'
    ])

if 'test_entries' not in st.session_state:
    st.session_state['test_entries'] = pd.DataFrame(columns=[
        'Date', 'Order No', 'Product Code', 'Test Type', 
        'Left Pass', 'Right Pass', 'Left Fail', 'Right Fail', 
        'Good Pairs', 'Total Fail', 'Operator', 'Remarks'
    ])

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['role'] = ""

# --- 1. LOGIN MODULE ---
def login_screen():
    st.title("🔐 System Login - Production Management")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username (admin / supervisor / operator)")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
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

if not st.session_state['logged_in']:
    login_screen()
else:
    # Sidebar Navigation
    st.sidebar.title(f"User: {st.session_state['username'].capitalize()}")
    st.sidebar.write(f"Role: **{st.session_state['role']}**")
    
    menu = ["Dashboard", "Order Management", "Test Entry", "Reports"]
    choice = st.sidebar.selectbox("Navigation Menu", menu)
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    role = st.session_state['role']

    # --- 2. ORDER MANAGEMENT ---
    if choice == "Order Management":
        st.header("📦 Order Management")
        
        if role in ["Admin", "Supervisor"]:
            tab1, tab2 = st.tabs(["➕ Add Single Order", "📂 Upload from Excel"])
            
            with tab1:
                with st.form("order_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        order_no = st.text_input("Order No")
                        cust_name = st.text_input("Customer Name")
                        prod_code = st.text_input("Product Code")
                    with col2:
                        qty = st.number_input("Test Quantity", min_value=1, value=100)
                        order_date = st.date_input("Order Date", datetime.today())
                        delivery_date = st.date_input("Delivery Date", datetime.today())
                    
                    submit_order = st.form_submit_button("Add Order")
                    if submit_order:
                        if order_no and prod_code:
                            new_row = pd.DataFrame({
                                'Order No': [str(order_no)],
                                'Customer Name': [str(cust_name)],
                                'Product Code': [str(prod_code)],
                                'Quantity': [int(qty)],
                                'Order Date': [str(order_date)],
                                'Delivery Date': [str(delivery_date)]
                            })
                            st.session_state['orders'] = pd.concat([st.session_state['orders'], new_row], ignore_index=True)
                            st.success("Order added successfully!")
                        else:
                            st.warning("Please fill Order No and Product Code.")
            
            with tab2:
                st.info("Upload an Excel file (.xlsx) containing orders. Columns needed: **Order No, Customer Name, Product Code, Quantity, Order Date, Delivery Date**")
                
                uploaded_excel = st.file_uploader("Upload Orders Excel File", type=["xlsx", "xls"])
                if uploaded_excel is not None:
                    try:
                        excel_df = pd.read_excel(uploaded_excel)
                        
                        # Clean column names (remove extra spaces)
                        excel_df.columns = excel_df.columns.astype(str).str.strip()
                        
                        expected_cols = ['Order No', 'Customer Name', 'Product Code', 'Quantity', 'Order Date', 'Delivery Date']
                        
                        if all(col in excel_df.columns for col in expected_cols):
                            st.write("Preview of uploaded orders:")
                            st.dataframe(excel_df.head(), use_container_width=True)
                            
                            if st.button("Confirm and Import Orders"):
                                excel_df['Order No'] = excel_df['Order No'].astype(str)
                                excel_df['Quantity'] = excel_df['Quantity'].astype(int)
                                
                                st.session_state['orders'] = pd.concat([st.session_state['orders'], excel_df[expected_cols]], ignore_index=True)
                                st.session_state['orders'] = st.session_state['orders'].drop_duplicates(subset=['Order No'], keep='last')
                                st.success("Orders imported successfully from Excel!")
                                st.rerun()
                        else:
                            st.error(f"Excel columns must exactly contain: {expected_cols}. Current columns found: {list(excel_df.columns)}")
                    except Exception as e:
                        st.error(f"Error reading file: {e}")    
        
        st.subheader("Existing Orders List")
        if not st.session_state['orders'].empty:
            st.dataframe(st.session_state['orders'], use_container_width=True)
            
            if role == "Admin" and st.button("Clear All Orders"):
                st.session_state['orders'] = pd.DataFrame(columns=st.session_state['orders'].columns)
                st.success("Orders cleared.")
                st.rerun()
        else:
            st.info("No orders found.")

    # --- 3. TEST ENTRY ---
    elif choice == "Test Entry":
        st.header("🧪 Test Entry & Quality Control")
        
        orders_df = st.session_state['orders']
        if orders_df.empty:
            st.warning("Please add orders in 'Order Management' first!")
        else:
            with st.form("test_form"):
                col1, col2 = st.columns(2)
                with col1:
                    test_date = st.date_input("Date", datetime.today())
                    order_no_sel = st.selectbox("Order No", orders_df['Order No'].unique())
                    
                    matching_products = orders_df[orders_df['Order No'] == order_no_sel]['Product Code'].unique()
                    prod_code = st.selectbox("Product Code", matching_products)
                    
                    test_type = st.selectbox("Test Type", ["Leak Test", "Visual Check", "Dimension Test", "Final QC"])
                
                with col2:
                    l_pass = st.number_input("Left Pass", min_value=0, value=0)
                    r_pass = st.number_input("Right Pass", min_value=0, value=0)
                    l_fail = st.number_input("Left Fail", min_value=0, value=0)
                    r_fail = st.number_input("Right Fail", min_value=0, value=0)
                    remarks = st.text_input("Remarks")
                
                submit_test = st.form_submit_button("Save Test Entry")
                if submit_test:
                    good_pairs = min(l_pass, r_pass)
                    total_fail = l_fail + r_fail
                    operator = st.session_state['username']
                    
                    new_test = pd.DataFrame({
                        'Date': [str(test_date)],
                        'Order No': [str(order_no_sel)],
                        'Product Code': [str(prod_code)],
                        'Test Type': [str(test_type)],
                        'Left Pass': [int(l_pass)],
                        'Right Pass': [int(r_pass)],
                        'Left Fail': [int(l_fail)],
                        'Right Fail': [int(r_fail)],
                        'Good Pairs': [int(good_pairs)],
                        'Total Fail': [int(total_fail)],
                        'Operator': [str(operator)],
                        'Remarks': [str(remarks)]
                    })
                    st.session_state['test_entries'] = pd.concat([st.session_state['test_entries'], new_test], ignore_index=True)
                    st.success(f"Test saved! Calculated Good Pairs: {good_pairs}")
                    st.rerun()

        st.subheader("Recent Test Entries (Manage & Delete)")
        if not st.session_state['test_entries'].empty:
            # Display test entries with index numbers for deletion reference
            test_df_display = st.session_state['test_entries'].copy()
            test_df_display.insert(0, 'Index', test_df_display.index)
            st.dataframe(test_df_display, use_container_width=True)
            
            # Delete row option
            col_del1, col_del2 = st.columns([2, 1])
            with col_del1:
                row_to_delete = st.selectbox("Select Index of Test Entry to Delete", options=test_df_display['Index'].tolist())
            with col_del2:
                st.write("")
                st.write("")
                if st.button("🗑️ Delete Selected Entry"):
                    st.session_state['test_entries'] = st.session_state['test_entries'].drop(row_to_delete).reset_index(drop=True)
                    st.success(f"Test entry at index {row_to_delete} deleted successfully!")
                    st.rerun()
        else:
            st.info("No test entries recorded yet.")

    # --- 5. DASHBOARD ---
    elif choice == "Dashboard":
        st.header("📊 Production Dashboard")
        
        orders_df = st.session_state['orders']
        tests_df = st.session_state['test_entries']
        
        total_orders = len(orders_df)
        total_target_qty = orders_df['Quantity'].astype(int).sum() if not orders_df.empty else 0
        total_good_pairs = tests_df['Good Pairs'].astype(int).sum() if not tests_df.empty else 0
        total_fails = tests_df['Total Fail'].astype(int).sum() if not tests_df.empty else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Orders", total_orders)
        col2.metric("Target Qty", total_target_qty)
        col3.metric("Total Good Pairs", total_good_pairs)
        col4.metric("Total Fails", total_fails)
        
        st.markdown("---")
        st.subheader("Production Progress Summary")
        if not tests_df.empty:
            chart_data = tests_df.groupby('Order No')[['Good Pairs', 'Total Fail']].sum()
            st.bar_chart(chart_data)
        else:
            st.info("Charts will appear once test entries are added.")

    # --- 6. REPORTS ---
    elif choice == "Reports":
        st.header("📈 Reports & Summary")
        
        tests_df = st.session_state['test_entries']
        orders_df = st.session_state['orders']
        
        if not tests_df.empty:
            st.subheader("Summary Report (Grouped by Order No, Customer & Product Code)")
            
            # Merge test entries with orders to get Customer Name
            if not orders_df.empty and 'Customer Name' in orders_df.columns:
                merged_df = pd.merge(tests_df, orders_df[['Order No', 'Customer Name']], on='Order No', how='left')
            else:
                merged_df = tests_df.copy()
                merged_df['Customer Name'] = ""
            
            # Group by Order No, Customer Name, Product Code, and Test Type, then sum the numeric columns
            grouped_df = merged_df.groupby(['Order No', 'Customer Name', 'Product Code', 'Test Type'])[[
                'Left Pass', 'Right Pass', 'Left Fail', 'Right Fail', 'Good Pairs', 'Total Fail'
            ]].sum().reset_index()
            
            st.dataframe(grouped_df, use_container_width=True)
            
            # Excel Export Button for Grouped Summary
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                grouped_df.to_excel(writer, index=False, sheet_name='Production_Summary')
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 Download Summary Report as Excel",
                data=excel_data,
                file_name="Production_Summary_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.markdown("---")
            with st.expander("View All Raw Test Entries (Detailed Log)"):
                st.dataframe(tests_df, use_container_width=True)
        else:
            st.info("No data available to generate reports.")