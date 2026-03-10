import streamlit as st
import pandas as pd
import os
import shutil
from datetime import datetime

# ==========================================
# 1. DUMMY FUNCTIONS FOR PROCESSING
# ==========================================
def process_cash_available_row(val1, val2, val3):
    """Function to process the variables from Tab 1"""
    st.success("Function called successfully!")
    st.write(f"**Processed Variables:** Var 1: `{val1}`, Var 2: `{val2}`, Var 3: `{val3}`")

def process_cash_unavailable_file(filename):
    """Function to process the filename from Tab 2"""
    st.success(f"Processing initiated for file: `{filename}`")

# ==========================================
# 2. SETUP DIRECTORIES & DUMMY DATA 
# (Ensures the app runs smoothly out-of-the-box)
# ==========================================
DATA_FILE = "cash_available.csv"
UNAVAILABLE_DIR = "unavailable_csvs"
EXPORT_DIR = "export_folder"
ARCHIVE_DIR = "archive_folder"

# Create required folders
for folder in[UNAVAILABLE_DIR, EXPORT_DIR, ARCHIVE_DIR]:
    os.makedirs(folder, exist_ok=True)

# Generate dummy CSV for Tab 1
if not os.path.exists(DATA_FILE):
    pd.DataFrame({
        "Transaction ID": [101, 102, 103],
        "Account":["Alpha", "Beta", "Gamma"],
        "Amount":[1500.0, 2400.5, 300.0]
    }).to_csv(DATA_FILE, index=False)

# Generate dummy CSVs for Tab 2
if not os.listdir(UNAVAILABLE_DIR):
    pd.DataFrame({"Sample": [1]}).to_csv(os.path.join(UNAVAILABLE_DIR, "missing_funds_jan.csv"), index=False)
    pd.DataFrame({"Sample": [2]}).to_csv(os.path.join(UNAVAILABLE_DIR, "missing_funds_feb.csv"), index=False)

# Generate a dummy Export Excel file for Tab 3
if not os.listdir(EXPORT_DIR):
    pd.DataFrame({"Status": ["Initial System Export"]}).to_excel(
        os.path.join(EXPORT_DIR, "export_data.xlsx"), index=False
    )

# ==========================================
# 3. STREAMLIT UI & TABS
# ==========================================
st.title("Financial Operations Dashboard")

tab1, tab2, tab3 = st.tabs(["Cash Available", "Cash Unavailable", "Export / Import"])

# ------------------------------------------
# TAB 1: Cash Available
# ------------------------------------------
with tab1:
    st.header("Cash Available")
    
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        
        st.write("Select a row from the table below:")
        # Display the dataframe with single-row selection (Requires Streamlit >= 1.35.0)
        event = st.dataframe(
            df,
            on_select="rerun",
            selection_mode="single_row",
            use_container_width=True
        )
        
        selected_rows = event.selection.rows
        
        if st.button("Next", key="next_tab1"):
            if selected_rows:
                # Get the index of the selected row
                row_idx = selected_rows[0]
                
                # Extract values from the row and store them in distinct variables
                var_transaction_id = df.iloc[row_idx]["Transaction ID"]
                var_account = df.iloc[row_idx]["Account"]
                var_amount = df.iloc[row_idx]["Amount"]
                
                # Pass the distinct variables to the function
                process_cash_available_row(var_transaction_id, var_account, var_amount)
            else:
                st.warning("Please select a row by clicking on it before hitting Next.")
    else:
        st.error(f"File '{DATA_FILE}' not found.")

# ------------------------------------------
# TAB 2: Cash Unavailable
# ------------------------------------------
with tab2:
    st.header("Cash Unavailable")
    
    # Read all CSV files located in the target directory
    csv_files =[f for f in os.listdir(UNAVAILABLE_DIR) if f.endswith('.csv')]
    
    if csv_files:
        selected_file = st.selectbox("Select a CSV file to process", csv_files)
        
        if st.button("Next", key="next_tab2"):
            # Pass the selected file name to the function
            process_cash_unavailable_file(selected_file)
    else:
        st.info("No CSV files found in the specified folder.")

# ------------------------------------------
# TAB 3: Export / Import
# ------------------------------------------
with tab3:
    st.header("Export / Import Management")
    
    # Identify the current export file residing in the Export Folder
    export_files =[f for f in os.listdir(EXPORT_DIR) if f.endswith(('.xlsx', '.xls'))]
    current_export_file = export_files[0] if export_files else None
    
    st.subheader("1. Export Current File")
    if current_export_file:
        file_path = os.path.join(EXPORT_DIR, current_export_file)
        
        # Read file as bytes for the download button
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        
        st.download_button(
            label="⬇️ Export Data",
            data=file_bytes,
            file_name=current_export_file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No export file currently available in the system.")
        
    st.divider()
    
    st.subheader("2. Import & Replace")
    uploaded_file = st.file_uploader("Upload an Excel file to replace the existing export file", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        if st.button("⬆️ Import File"):
            # Step 1: Move the existing export file to the archive folder
            if current_export_file:
                for existing_file in export_files:
                    src_path = os.path.join(EXPORT_DIR, existing_file)
                    dest_path = os.path.join(ARCHIVE_DIR, existing_file)
                    shutil.move(src_path, dest_path)
            
            # Step 2: Extract details and prepare new timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_name, ext = os.path.splitext(uploaded_file.name)
            new_filename = f"{original_name}_{timestamp}{ext}"
            new_file_path = os.path.join(EXPORT_DIR, new_filename)
            
            # Step 3: Save the uploaded file in the export folder
            with open(new_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            st.success(f"File successfully imported and saved as `{new_filename}`. Previous file moved to archive.")
            
            # Refresh the page to update the Export download button
            st.rerun()
