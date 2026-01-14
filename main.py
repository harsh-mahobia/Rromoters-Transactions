import streamlit as st
import pandas as pd
import io

# Page configuration
st.set_page_config(
    page_title="CSV Uploader & Viewer",
    page_icon="📊",
    layout="wide"
)

# Required columns for the CSV file
REQUIRED_COLUMNS = [
    'SYMBOL',
    'COMPANY',
    'REGULATION',
    'NAME OF THE ACQUIRER/DISPOSER',
    'CATEGORY OF PERSON',
    'TYPE OF SECURITY (PRIOR)',
    'NO. OF SECURITY (PRIOR)',
    '% SHAREHOLDING (PRIOR)',
    'TYPE OF SECURITY (ACQUIRED/DISPLOSED)',
    'NO. OF SECURITIES (ACQUIRED/DISPLOSED)',
    'VALUE OF SECURITY (ACQUIRED/DISPLOSED)',
    'ACQUISITION/DISPOSAL TRANSACTION TYPE',
    'TYPE OF SECURITY (POST)',
    'NO. OF SECURITY (POST)',
    '% POST',
    'DATE OF ALLOTMENT/ACQUISITION FROM',
    'DATE OF ALLOTMENT/ACQUISITION TO',
    'DATE OF INITMATION TO COMPANY',
    'MODE OF ACQUISITION',
    'DERIVATIVE TYPE SECURITY',
    'DERIVATIVE CONTRACT SPECIFICATION',
    'NOTIONAL VALUE(BUY)',
    'NUMBER OF UNITS/CONTRACT LOT SIZE (BUY)',
    'NOTIONAL VALUE(SELL)',
    'NUMBER OF UNITS/CONTRACT LOT SIZE  (SELL)',
    'EXCHANGE',
    'REMARK',
    'BROADCASTE DATE AND TIME',
    'XBRL'
]

# Title
st.title("📊 CSV Uploader & Data Viewer")
st.markdown("---")

# Initialize session state for storing dataframe
if 'df' not in st.session_state:
    st.session_state.df = None

# File uploader
uploaded_file = st.file_uploader(
    "Choose a CSV file",
    type=['csv'],
    help="Upload a CSV file to view and analyze its data"
)

# Process uploaded file
if uploaded_file is not None:
    try:
        # Read CSV file
        df = pd.read_csv(uploaded_file)
        
        # Clean column names (strip whitespace)
        df.columns = df.columns.str.strip()
        
        # Validate columns
        uploaded_columns = set(df.columns)
        required_columns_set = set(REQUIRED_COLUMNS)
        
        # Check if all required columns are present
        missing_columns = required_columns_set - uploaded_columns
        extra_columns = uploaded_columns - required_columns_set
        
        if missing_columns:
            st.error(f"❌ Invalid CSV file! Missing required columns: {', '.join(sorted(missing_columns))}")
            st.warning(f"📋 Required columns ({len(REQUIRED_COLUMNS)}):")
            st.code('\n'.join([f"{i+1}. {col}" for i, col in enumerate(REQUIRED_COLUMNS)]))
            st.stop()
        
        if extra_columns:
            st.warning(f"⚠️ File contains extra columns that will be ignored: {', '.join(sorted(extra_columns))}")
            # Keep only required columns
            df = df[REQUIRED_COLUMNS]
        
        # Ensure columns are in the correct order
        df = df[REQUIRED_COLUMNS]
        
        # Store original dataframe for reference
        original_count = len(df)
        
        # Apply automatic filters
        # Filter 1: Remove REGULATION of type 7(3) (handle whitespace)
        df = df[df['REGULATION'].astype(str).str.strip() != '7(3)']
        regulation_filtered_count = len(df)
        
        # Filter 2: Only keep CATEGORY OF PERSON as "Promoter Group" or "Promoters"
        # Case-insensitive matching, handle NaN values
        df = df[df['CATEGORY OF PERSON'].notna() & 
                df['CATEGORY OF PERSON'].astype(str).str.strip().str.lower().isin(['promoter group', 'promoters'])]
        final_count = len(df)
        
        # Store filtered dataframe
        st.session_state.df = df
        
        # Display success message with filter info
        st.success(f"✅ File uploaded successfully! ({final_count} rows, {len(df.columns)} columns)")
        
        # Show filter information
        if original_count != final_count:
            st.info(f"📊 **Filters Applied:** Removed {original_count - regulation_filtered_count} rows with REGULATION '7(3)' and {regulation_filtered_count - final_count} rows with other CATEGORY OF PERSON values. Showing {final_count} filtered rows.")
        
        # Show basic info
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Rows", final_count)
        with col2:
            st.metric("Total Columns", len(df.columns))
        with col3:
            st.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB")
        with col4:
            st.metric("Missing Values", df.isnull().sum().sum())
        
        st.markdown("---")
        
        # Dropdown for column selection
        st.subheader("🔽 Additional Column Selection & Filtering")
        st.caption("ℹ️ Automatic filters already applied: REGULATION ≠ '7(3)' and CATEGORY OF PERSON = 'Promoter Group' or 'Promoters'")
        
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            # Multi-select dropdown for columns
            selected_columns = st.multiselect(
                "Select columns to display:",
                options=df.columns.tolist(),
                default=df.columns.tolist(),
                help="Choose which columns you want to see in the data table"
            )
        
        with col_right:
            # Dropdown for filtering by column (optional)
            filter_column = st.selectbox(
                "Filter by column (optional):",
                options=["None"] + df.columns.tolist(),
                help="Select a column to filter the data"
            )
        
        # Apply filters
        filtered_df = df.copy()
        
        # Column selection
        if selected_columns:
            filtered_df = filtered_df[selected_columns]
        else:
            st.warning("⚠️ Please select at least one column to display.")
            filtered_df = pd.DataFrame()
        
        # Column-based filtering
        if filter_column != "None" and len(filtered_df) > 0:
            unique_values = df[filter_column].dropna().unique().tolist()
            if len(unique_values) > 0:
                selected_filter_value = st.selectbox(
                    f"Select value from '{filter_column}':",
                    options=["All"] + sorted([str(v) for v in unique_values]),
                    help=f"Filter rows where {filter_column} equals the selected value"
                )
                
                if selected_filter_value != "All":
                    filtered_df = filtered_df[df[filter_column] == selected_filter_value]
        
        st.markdown("---")
        
        # Display data
        if len(filtered_df) > 0:
            st.subheader("📋 Data Preview")
            
            # Show data info
            st.info(f"Showing {len(filtered_df)} rows and {len(filtered_df.columns)} columns")
            
            # Display dataframe
            st.dataframe(
                filtered_df,
                use_container_width=True,
                height=400
            )
            
            # Download filtered data
            csv_buffer = io.StringIO()
            filtered_df.to_csv(csv_buffer, index=False)
            csv_string = csv_buffer.getvalue()
            
            st.download_button(
                label="📥 Download Filtered Data as CSV",
                data=csv_string,
                file_name="filtered_data.csv",
                mime="text/csv"
            )
        else:
            st.warning("No data to display. Please adjust your filters.")
        
        # Additional information section
        with st.expander("📊 Data Statistics"):
            st.subheader("Column Information")
            st.dataframe(df.describe(), use_container_width=True)
            
            st.subheader("Data Types")
            dtype_df = pd.DataFrame({
                'Column': df.columns,
                'Data Type': [str(dtype) for dtype in df.dtypes],
                'Non-Null Count': df.count().values,
                'Null Count': df.isnull().sum().values
            })
            st.dataframe(dtype_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error reading CSV file: {str(e)}")
        st.info("Please make sure you uploaded a valid CSV file.")

else:
    # Instructions when no file is uploaded
    st.info("👆 Please upload a CSV file to get started.")
    
    # Show required columns
    st.markdown("### 📋 Required CSV Format:")
    st.info(f"This application accepts CSV files with exactly **{len(REQUIRED_COLUMNS)} columns** as listed below:")
    
    # Display required columns in a nice format
    cols_display = pd.DataFrame({
        'Column Number': range(1, len(REQUIRED_COLUMNS) + 1),
        'Column Name': REQUIRED_COLUMNS
    })
    st.dataframe(cols_display, use_container_width=True, hide_index=True)
    
    st.markdown("**Note:** Column order doesn't matter, but all columns must be present in the uploaded file.")
