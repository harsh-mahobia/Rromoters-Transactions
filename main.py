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
        
        #TODO: anything after promoter should be there.
        # Filter 2: Only keep CATEGORY OF PERSON as "Promoter Group" or "Promoters"
        # Case-insensitive matching, handle NaN values
        df = df[df['CATEGORY OF PERSON'].notna() & 
                df['CATEGORY OF PERSON'].astype(str).str.strip().str.lower().isin(['promoter group', 'promoters'])]
        category_filtered_count = len(df)
        
        # Filter 3: Only keep ACQUISITION/DISPOSAL TRANSACTION TYPE as "Buy" or "Sell"
        # Case-insensitive matching, handle NaN values
        df = df[df['ACQUISITION/DISPOSAL TRANSACTION TYPE'].notna() & 
                df['ACQUISITION/DISPOSAL TRANSACTION TYPE'].astype(str).str.strip().str.lower().isin(['buy', 'sell'])]
        transaction_filtered_count = len(df)
        
        # Filter 4: Only keep MODE OF ACQUISITION as "Market Sale" or "Market Purchase"
        # Case-insensitive matching, handle NaN values
        df = df[df['MODE OF ACQUISITION'].notna() & 
                df['MODE OF ACQUISITION'].astype(str).str.strip().str.lower().isin(['market sale', 'market purchase'])]
        mode_filtered_count = len(df)
        
        # Filter 5: Only keep TYPE OF SECURITY (PRIOR) as "Equity Shares"
        # Case-insensitive matching, handle NaN values and variations
        # Convert to string, strip whitespace, lowercase, and check for equity share(s)
        security_prior_col = df['TYPE OF SECURITY (PRIOR)'].astype(str).str.strip().str.lower()
        df = df[(df['TYPE OF SECURITY (PRIOR)'].notna()) & 
                (security_prior_col.str.contains('equity share', na=False))]
        final_count = len(df)
        
        # Remove specified columns
        columns_to_remove = [
            'DERIVATIVE TYPE SECURITY',
            'DERIVATIVE CONTRACT SPECIFICATION',
            'NOTIONAL VALUE(BUY)',
            'NUMBER OF UNITS/CONTRACT LOT SIZE (BUY)',
            'NOTIONAL VALUE(SELL)',
            'NUMBER OF UNITS/CONTRACT LOT SIZE  (SELL)',
            'REMARK',
            'BROADCASTE DATE AND TIME',
            'XBRL',
            'TYPE OF SECURITY (ACQUIRED/DISPLOSED)'
        ]
        
        # Remove columns that exist in the dataframe
        existing_columns_to_remove = [col for col in columns_to_remove if col in df.columns]
        if existing_columns_to_remove:
            df = df.drop(columns=existing_columns_to_remove)
        
        # Store filtered dataframe
        st.session_state.df = df
        
        # Display success message with filter info
        st.success(f"✅ File uploaded successfully! ({final_count} rows, {len(df.columns)} columns)")
        
        # Show filter information
        if original_count != final_count:
            filter_info = []
            if original_count != regulation_filtered_count:
                filter_info.append(f"{original_count - regulation_filtered_count} rows with REGULATION '7(3)'")
            if regulation_filtered_count != category_filtered_count:
                filter_info.append(f"{regulation_filtered_count - category_filtered_count} rows with other CATEGORY OF PERSON values")
            if category_filtered_count != transaction_filtered_count:
                filter_info.append(f"{category_filtered_count - transaction_filtered_count} rows with other ACQUISITION/DISPOSAL TRANSACTION TYPE values")
            if transaction_filtered_count != mode_filtered_count:
                filter_info.append(f"{transaction_filtered_count - mode_filtered_count} rows with other MODE OF ACQUISITION values")
            if mode_filtered_count != final_count:
                filter_info.append(f"{mode_filtered_count - final_count} rows with other TYPE OF SECURITY (PRIOR) values")
            
            st.info(f"📊 **Filters Applied:** Removed {', '.join(filter_info)}. Showing {final_count} filtered rows.")
        
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
        st.caption("ℹ️ Automatic filters already applied: REGULATION ≠ '7(3)', CATEGORY OF PERSON = 'Promoter Group' or 'Promoters', ACQUISITION/DISPOSAL TRANSACTION TYPE = 'Buy' or 'Sell', MODE OF ACQUISITION = 'Market Sale' or 'Market Purchase', and TYPE OF SECURITY (PRIOR) = 'Equity Shares'")
        
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
        
        # Transactions Analytics Section
        st.markdown("---")
        st.subheader("📈 Transactions Analytics")
        
        # Show number of distinct companies
        if len(df) > 0 and 'COMPANY' in df.columns:
            distinct_companies = df['COMPANY'].nunique()
            st.caption(f"📊 **{distinct_companies}** distinct companies")
        
        if len(df) > 0:
            try:
                # Prepare data for transactions analysis
                transactions_df = df.copy()
                
                # Check if required columns exist before processing
                if 'NO. OF SECURITIES (ACQUIRED/DISPLOSED)' not in transactions_df.columns:
                    st.error("❌ Column 'NO. OF SECURITIES (ACQUIRED/DISPLOSED)' not found in the data.")
                    st.info(f"Available columns: {', '.join(sorted(transactions_df.columns.tolist()))}")
                elif 'VALUE OF SECURITY (ACQUIRED/DISPLOSED)' not in transactions_df.columns:
                    st.error("❌ Column 'VALUE OF SECURITY (ACQUIRED/DISPLOSED)' not found in the data.")
                    st.info(f"Available columns: {', '.join(sorted(transactions_df.columns.tolist()))}")
                elif 'COMPANY' not in transactions_df.columns:
                    st.error("❌ Column 'COMPANY' not found in the data.")
                    st.info(f"Available columns: {', '.join(sorted(transactions_df.columns.tolist()))}")
                elif 'ACQUISITION/DISPOSAL TRANSACTION TYPE' not in transactions_df.columns:
                    st.error("❌ Column 'ACQUISITION/DISPOSAL TRANSACTION TYPE' not found in the data.")
                    st.info(f"Available columns: {', '.join(sorted(transactions_df.columns.tolist()))}")
                else:
                    # Convert numeric columns, handling any non-numeric values
                    transactions_df['NO. OF SECURITIES (ACQUIRED/DISPLOSED)'] = pd.to_numeric(
                        transactions_df['NO. OF SECURITIES (ACQUIRED/DISPLOSED)'], 
                        errors='coerce'
                    )
                    transactions_df['VALUE OF SECURITY (ACQUIRED/DISPLOSED)'] = pd.to_numeric(
                        transactions_df['VALUE OF SECURITY (ACQUIRED/DISPLOSED)'], 
                        errors='coerce'
                    )
                    
                    # Group by company and transaction type
                    transaction_type_upper = transactions_df['ACQUISITION/DISPOSAL TRANSACTION TYPE'].astype(str).str.strip().str.upper()
                    buy_data = transactions_df[transaction_type_upper == 'BUY']
                    sell_data = transactions_df[transaction_type_upper == 'SELL']
                    
                    # Calculate totals by company for Buy transactions
                    if len(buy_data) > 0:
                        buy_summary = buy_data.groupby('COMPANY').agg({
                            'NO. OF SECURITIES (ACQUIRED/DISPLOSED)': 'sum',
                            'VALUE OF SECURITY (ACQUIRED/DISPLOSED)': 'sum'
                        }).reset_index()
                        buy_summary.columns = ['COMPANY', 'Shares Buy', 'Amount of Shares Buy']
                    else:
                        buy_summary = pd.DataFrame(columns=['COMPANY', 'Shares Buy', 'Amount of Shares Buy'])
                    
                    # Calculate totals by company for Sell transactions
                    if len(sell_data) > 0:
                        sell_summary = sell_data.groupby('COMPANY').agg({
                            'NO. OF SECURITIES (ACQUIRED/DISPLOSED)': 'sum',
                            'VALUE OF SECURITY (ACQUIRED/DISPLOSED)': 'sum'
                        }).reset_index()
                        sell_summary.columns = ['COMPANY', 'Shares Sell', 'Amount of Shares Sell']
                    else:
                        sell_summary = pd.DataFrame(columns=['COMPANY', 'Shares Sell', 'Amount of Shares Sell'])
                    
                    # Merge buy and sell summaries
                    if len(buy_summary) > 0 and len(sell_summary) > 0:
                        transactions_summary = pd.merge(
                            buy_summary,
                            sell_summary,
                            on='COMPANY',
                            how='outer'
                        ).fillna(0)
                    elif len(buy_summary) > 0:
                        transactions_summary = buy_summary.copy()
                        transactions_summary['Shares Sell'] = 0
                        transactions_summary['Amount of Shares Sell'] = 0
                    elif len(sell_summary) > 0:
                        transactions_summary = sell_summary.copy()
                        transactions_summary['Shares Buy'] = 0
                        transactions_summary['Amount of Shares Buy'] = 0
                    else:
                        transactions_summary = pd.DataFrame(columns=['COMPANY', 'Shares Buy', 'Amount of Shares Buy', 'Shares Sell', 'Amount of Shares Sell'])
                    
                    if len(transactions_summary) > 0:
                        # Sort by company name
                        transactions_summary = transactions_summary.sort_values('COMPANY').reset_index(drop=True)
                        
                        # Format the numbers for better display
                        transactions_summary['Shares Buy'] = transactions_summary['Shares Buy'].fillna(0).astype(int)
                        transactions_summary['Shares Sell'] = transactions_summary['Shares Sell'].fillna(0).astype(int)
                        transactions_summary['Amount of Shares Buy'] = transactions_summary['Amount of Shares Buy'].fillna(0).round(2)
                        transactions_summary['Amount of Shares Sell'] = transactions_summary['Amount of Shares Sell'].fillna(0).round(2)
                        
                        # Display the transactions summary
                        st.dataframe(
                            transactions_summary,
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Download button for transactions summary
                        transactions_csv_buffer = io.StringIO()
                        transactions_summary.to_csv(transactions_csv_buffer, index=False)
                        transactions_csv_string = transactions_csv_buffer.getvalue()
                        
                        st.download_button(
                            label="📥 Download Transactions Summary as CSV",
                            data=transactions_csv_string,
                            file_name="transactions_summary.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("No transaction data available to display.")
                
            except KeyError as e:
                missing_col = str(e).strip("'")
                st.error(f"❌ Missing required column for transactions analysis: {missing_col}")
                st.info(f"Available columns: {', '.join(sorted(df.columns.tolist()))}")
            except Exception as e:
                st.error(f"❌ Error generating transactions analytics: {str(e)}")
                st.info("Please ensure the data contains valid numeric values for shares and amounts.")
        else:
            st.info("No data available for transactions analysis.")
        
        # Max Transactions Section
        st.markdown("---")
        st.subheader("📊 Max Transactions")
        
        if len(df) > 0:
            try:
                # Check if required columns exist
                required_cols_max = ['COMPANY', 'NO. OF SECURITIES (ACQUIRED/DISPLOSED)', 
                                   'VALUE OF SECURITY (ACQUIRED/DISPLOSED)', 
                                   'ACQUISITION/DISPOSAL TRANSACTION TYPE',
                                   'DATE OF ALLOTMENT/ACQUISITION FROM']
                missing_cols_max = [col for col in required_cols_max if col not in df.columns]
                
                if missing_cols_max:
                    st.error(f"❌ Missing required columns for max transactions analysis: {', '.join(missing_cols_max)}")
                    st.info(f"Available columns: {', '.join(sorted(df.columns.tolist()))}")
                else:
                    # Prepare data for max transactions analysis
                    max_transactions_df = df.copy()
                    
                    # Convert numeric columns
                    max_transactions_df['NO. OF SECURITIES (ACQUIRED/DISPLOSED)'] = pd.to_numeric(
                        max_transactions_df['NO. OF SECURITIES (ACQUIRED/DISPLOSED)'], 
                        errors='coerce'
                    )
                    max_transactions_df['VALUE OF SECURITY (ACQUIRED/DISPLOSED)'] = pd.to_numeric(
                        max_transactions_df['VALUE OF SECURITY (ACQUIRED/DISPLOSED)'], 
                        errors='coerce'
                    )
                    
                    # Separate buy and sell transactions
                    transaction_type_upper = max_transactions_df['ACQUISITION/DISPOSAL TRANSACTION TYPE'].astype(str).str.strip().str.upper()
                    buy_data_max = max_transactions_df[transaction_type_upper == 'BUY'].copy()
                    sell_data_max = max_transactions_df[transaction_type_upper == 'SELL'].copy()
                    
                    max_transactions_list = []
                    
                    # Get unique companies
                    unique_companies = max_transactions_df['COMPANY'].unique()
                    
                    for company in unique_companies:
                        company_buy = buy_data_max[buy_data_max['COMPANY'] == company]
                        company_sell = sell_data_max[sell_data_max['COMPANY'] == company]
                        
                        max_transaction = {'COMPANY': company}
                        
                        # Max Buy Amount and Date
                        if len(company_buy) > 0:
                            buy_value_col = company_buy['VALUE OF SECURITY (ACQUIRED/DISPLOSED)']
                            if buy_value_col.notna().any():
                                max_buy_idx = buy_value_col.idxmax()
                                if pd.notna(max_buy_idx):
                                    max_transaction['Max Buy Amount'] = company_buy.loc[max_buy_idx, 'VALUE OF SECURITY (ACQUIRED/DISPLOSED)']
                                    max_transaction['Max Buy Amount Date'] = company_buy.loc[max_buy_idx, 'DATE OF ALLOTMENT/ACQUISITION FROM']
                                else:
                                    max_transaction['Max Buy Amount'] = None
                                    max_transaction['Max Buy Amount Date'] = None
                            else:
                                max_transaction['Max Buy Amount'] = None
                                max_transaction['Max Buy Amount Date'] = None
                            
                            # Max Buy Shares and Date
                            # If multiple rows have same max shares, choose the one with highest value
                            buy_shares_col = company_buy['NO. OF SECURITIES (ACQUIRED/DISPLOSED)']
                            buy_value_col = company_buy['VALUE OF SECURITY (ACQUIRED/DISPLOSED)']
                            if buy_shares_col.notna().any():
                                max_shares_value = buy_shares_col.max()
                                # Find all rows with max shares
                                max_shares_rows = company_buy[buy_shares_col == max_shares_value]
                                if len(max_shares_rows) > 0:
                                    # Among rows with max shares, find the one with max value
                                    max_value_in_max_shares = max_shares_rows['VALUE OF SECURITY (ACQUIRED/DISPLOSED)'].max()
                                    if pd.notna(max_value_in_max_shares):
                                        max_shares_max_value_rows = max_shares_rows[
                                            max_shares_rows['VALUE OF SECURITY (ACQUIRED/DISPLOSED)'] == max_value_in_max_shares
                                        ]
                                        # Check if we have any rows after filtering
                                        if len(max_shares_max_value_rows) > 0:
                                            # Get the first row (or use idxmax if needed)
                                            max_buy_shares_idx = max_shares_max_value_rows.index[0]
                                            max_transaction['Max Buy Shares'] = company_buy.loc[max_buy_shares_idx, 'NO. OF SECURITIES (ACQUIRED/DISPLOSED)']
                                            max_transaction['Max Buy Shares Date'] = company_buy.loc[max_buy_shares_idx, 'DATE OF ALLOTMENT/ACQUISITION FROM']
                                        else:
                                            max_transaction['Max Buy Shares'] = None
                                            max_transaction['Max Buy Shares Date'] = None
                                    else:
                                        max_transaction['Max Buy Shares'] = None
                                        max_transaction['Max Buy Shares Date'] = None
                                else:
                                    max_transaction['Max Buy Shares'] = None
                                    max_transaction['Max Buy Shares Date'] = None
                            else:
                                max_transaction['Max Buy Shares'] = None
                                max_transaction['Max Buy Shares Date'] = None
                        else:
                            max_transaction['Max Buy Amount'] = None
                            max_transaction['Max Buy Amount Date'] = None
                            max_transaction['Max Buy Shares'] = None
                            max_transaction['Max Buy Shares Date'] = None
                        
                        # Max Sell Amount and Date
                        if len(company_sell) > 0:
                            sell_value_col = company_sell['VALUE OF SECURITY (ACQUIRED/DISPLOSED)']
                            if sell_value_col.notna().any():
                                max_sell_idx = sell_value_col.idxmax()
                                if pd.notna(max_sell_idx):
                                    max_transaction['Max Sell Amount'] = company_sell.loc[max_sell_idx, 'VALUE OF SECURITY (ACQUIRED/DISPLOSED)']
                                    max_transaction['Max Sell Amount Date'] = company_sell.loc[max_sell_idx, 'DATE OF ALLOTMENT/ACQUISITION FROM']
                                else:
                                    max_transaction['Max Sell Amount'] = None
                                    max_transaction['Max Sell Amount Date'] = None
                            else:
                                max_transaction['Max Sell Amount'] = None
                                max_transaction['Max Sell Amount Date'] = None
                            
                            # Max Sell Shares and Date
                            # If multiple rows have same max shares, choose the one with highest value
                            sell_shares_col = company_sell['NO. OF SECURITIES (ACQUIRED/DISPLOSED)']
                            sell_value_col = company_sell['VALUE OF SECURITY (ACQUIRED/DISPLOSED)']
                            if sell_shares_col.notna().any():
                                max_shares_value = sell_shares_col.max()
                                # Find all rows with max shares
                                max_shares_rows = company_sell[sell_shares_col == max_shares_value]
                                if len(max_shares_rows) > 0:
                                    # Among rows with max shares, find the one with max value
                                    max_value_in_max_shares = max_shares_rows['VALUE OF SECURITY (ACQUIRED/DISPLOSED)'].max()
                                    if pd.notna(max_value_in_max_shares):
                                        max_shares_max_value_rows = max_shares_rows[
                                            max_shares_rows['VALUE OF SECURITY (ACQUIRED/DISPLOSED)'] == max_value_in_max_shares
                                        ]
                                        # Check if we have any rows after filtering
                                        if len(max_shares_max_value_rows) > 0:
                                            # Get the first row (or use idxmax if needed)
                                            max_sell_shares_idx = max_shares_max_value_rows.index[0]
                                            max_transaction['Max Sell Shares'] = company_sell.loc[max_sell_shares_idx, 'NO. OF SECURITIES (ACQUIRED/DISPLOSED)']
                                            max_transaction['Max Sell Shares Date'] = company_sell.loc[max_sell_shares_idx, 'DATE OF ALLOTMENT/ACQUISITION FROM']
                                        else:
                                            max_transaction['Max Sell Shares'] = None
                                            max_transaction['Max Sell Shares Date'] = None
                                    else:
                                        max_transaction['Max Sell Shares'] = None
                                        max_transaction['Max Sell Shares Date'] = None
                                else:
                                    max_transaction['Max Sell Shares'] = None
                                    max_transaction['Max Sell Shares Date'] = None
                            else:
                                max_transaction['Max Sell Shares'] = None
                                max_transaction['Max Sell Shares Date'] = None
                        else:
                            max_transaction['Max Sell Amount'] = None
                            max_transaction['Max Sell Amount Date'] = None
                            max_transaction['Max Sell Shares'] = None
                            max_transaction['Max Sell Shares Date'] = None
                        
                        max_transactions_list.append(max_transaction)
                    
                    # Create dataframe
                    max_transactions_summary = pd.DataFrame(max_transactions_list)
                    max_transactions_summary = max_transactions_summary.sort_values('COMPANY').reset_index(drop=True)
                    
                    # Format the numbers
                    if 'Max Buy Amount' in max_transactions_summary.columns:
                        max_transactions_summary['Max Buy Amount'] = max_transactions_summary['Max Buy Amount'].fillna(0).round(2)
                    if 'Max Buy Shares' in max_transactions_summary.columns:
                        max_transactions_summary['Max Buy Shares'] = max_transactions_summary['Max Buy Shares'].fillna(0).astype(int)
                    if 'Max Sell Amount' in max_transactions_summary.columns:
                        max_transactions_summary['Max Sell Amount'] = max_transactions_summary['Max Sell Amount'].fillna(0).round(2)
                    if 'Max Sell Shares' in max_transactions_summary.columns:
                        max_transactions_summary['Max Sell Shares'] = max_transactions_summary['Max Sell Shares'].fillna(0).astype(int)
                    
                    # Display the max transactions summary
                    if len(max_transactions_summary) > 0:
                        st.dataframe(
                            max_transactions_summary,
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Download button for max transactions summary
                        max_transactions_csv_buffer = io.StringIO()
                        max_transactions_summary.to_csv(max_transactions_csv_buffer, index=False)
                        max_transactions_csv_string = max_transactions_csv_buffer.getvalue()
                        
                        st.download_button(
                            label="📥 Download Max Transactions Summary as CSV",
                            data=max_transactions_csv_string,
                            file_name="max_transactions_summary.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("No max transaction data available to display.")
                        
            except KeyError as e:
                # Better error message extraction
                error_msg = str(e)
                if "'" in error_msg:
                    missing_col = error_msg.strip("'\"")
                else:
                    missing_col = error_msg
                st.error(f"❌ Missing required column for max transactions analysis: {missing_col}")
                st.info(f"Available columns: {', '.join(sorted(df.columns.tolist()))}")
                st.error(f"Full error details: {repr(e)}")
            except Exception as e:
                st.error(f"❌ Error generating max transactions analytics: {str(e)}")
                st.error(f"Error type: {type(e).__name__}")
                st.info("Please ensure the data contains valid numeric values and dates.")
                import traceback
                st.code(traceback.format_exc())
        
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
