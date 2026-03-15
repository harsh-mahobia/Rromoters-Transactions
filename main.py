import streamlit as st
import pandas as pd
import io
import os
import pickle
from datetime import datetime

# Function to format numbers in Indian currency standard
def format_indian_number(num):
    """
    Format numbers according to Indian numbering system:
    - Thousand: 1,000
    - Lakh: 1,00,000
    - Crore: 1,00,00,000
    """
    if pd.isna(num):
        return num
    
    try:
        num = float(num)
        if num == 0:
            return "0"
        
        # Determine if negative
        is_negative = num < 0
        num = abs(num)
        
        # Split into integer and decimal parts
        num_str = f"{num:.2f}"
        integer_part, decimal_part = num_str.split('.')
        
        # Remove trailing zeros from decimal
        decimal_part = decimal_part.rstrip('0').rstrip('.')
        
        # Format integer part with Indian commas
        if len(integer_part) <= 3:
            formatted = integer_part
        else:
            # Last 3 digits
            last_three = integer_part[-3:]
            remaining = integer_part[:-3]
            
            # Add commas every 2 digits from right to left for remaining digits
            formatted_remaining = ''
            for i, digit in enumerate(reversed(remaining)):
                if i > 0 and i % 2 == 0:
                    formatted_remaining = ',' + formatted_remaining
                formatted_remaining = digit + formatted_remaining
            
            formatted = formatted_remaining + ',' + last_three
        
        # Add decimal part if exists
        if decimal_part:
            formatted = formatted + '.' + decimal_part
        
        # Add negative sign if needed
        if is_negative:
            formatted = '-' + formatted
        
        return formatted
    except (ValueError, TypeError):
        return num

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

# Source link with animation
st.markdown(
    """
    <style>
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    .source-link {
        display: inline-block;
        padding: 8px 16px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        text-decoration: none;
        border-radius: 20px;
        font-weight: 500;
        transition: all 0.3s ease;
        animation: pulse 2s ease-in-out infinite;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 0 10px 20px 10px;
    }
    .source-link:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
        animation: none;
    }
    .source-link.secondary {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    .source-container {
        text-align: center;
        margin: 10px 0;
    }
    </style>
    <div class="source-container">
        <a href="https://www.nseindia.com/companies-listing/corporate-filings-insider-trading" 
           target="_blank" 
           class="source-link">
            🔗 Data Source: NSE India - Corporate Filings Insider Trading
        </a>
        <a href="https://www.stockscans.in/scans" 
           target="_blank" 
           class="source-link secondary">
            📊 StockScans - Stock Screener & Analysis
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# ── Disk cache helpers ────────────────────────────────────────────────────────
CACHE_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')
CACHE_FILE = os.path.join(CACHE_DIR, 'app_state.pkl')

CAKEY_KEYS = ['df_main', 'combined_summary', 'filter_info_text',
               'last_processed_files', 'buy_max_indices', 'sell_max_indices',
               'last_processed_timestamp']

def load_cache():
    """Load persisted state from disk into session_state (only on first run)."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'rb') as f:
                saved = pickle.load(f)
            for k in CAKEY_KEYS:
                if k not in st.session_state and k in saved:
                    st.session_state[k] = saved[k]
        except Exception:
            pass  # corrupt cache – ignore silently

def save_cache():
    """Persist relevant session_state keys to disk."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    payload = {k: st.session_state.get(k) for k in CAKEY_KEYS}
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(payload, f)

# Load cache before initialising defaults so saved values aren't overwritten
load_cache()

# Initialize session state for persistent storage
if 'df_main' not in st.session_state: st.session_state.df_main = None
if 'combined_summary' not in st.session_state: st.session_state.combined_summary = None
if 'filter_info_text' not in st.session_state: st.session_state.filter_info_text = None
if 'last_processed_files' not in st.session_state: st.session_state.last_processed_files = (None, None)
if 'buy_max_indices' not in st.session_state: st.session_state.buy_max_indices = []
if 'sell_max_indices' not in st.session_state: st.session_state.sell_max_indices = []
if 'last_processed_timestamp' not in st.session_state: st.session_state.last_processed_timestamp = None

# File uploader
col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("1. Choose Transactions CSV file", type=['csv'], help="Upload the primary transaction CSV file")
with col2:
    fundamentals_file = st.file_uploader("2. Choose Fundamentals CSV file (Optional)", type=['csv'], help="Upload a fundamentals CSV file")

# Timestamp badge
_ts = st.session_state.last_processed_timestamp
if _ts:
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:8px;margin:6px 0 0 2px;">
            <span style="font-size:0.75rem;color:#a0a0a0;">Last processed:</span>
            <span style="
                background:linear-gradient(135deg,#1e3a5f,#2d5a8e);
                color:#90caf9;
                font-size:0.75rem;
                font-weight:600;
                padding:3px 10px;
                border-radius:12px;
                border:1px solid #2d5a8e;
                letter-spacing:0.03em;
            ">⏰ {_ts}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

# Track file changes to avoid redundant heavy processing
uploaded_id = f"{uploaded_file.name}_{uploaded_file.size}" if uploaded_file else None
fundamentals_id = f"{fundamentals_file.name}_{fundamentals_file.size}" if fundamentals_file else None
current_files = (uploaded_id, fundamentals_id)

files_changed = uploaded_file is not None and current_files != st.session_state.last_processed_files

# --- PROCESSING SECTION ---
if files_changed:
    try:
        with st.spinner("Processing files and calculating analytics..."):
            # 1. Read and Initial Clean
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip()
            if not set(REQUIRED_COLUMNS).issubset(set(df.columns)):
                st.error("❌ Missing required columns in uploaded CSV.")
                st.stop()
            df = df[REQUIRED_COLUMNS]
            original_count = len(df)
            
            # 2. Apply Automatic Filters
            df = df[df['REGULATION'].astype(str).str.strip() != '7(3)']
            reg_f = len(df)
            df = df[df['CATEGORY OF PERSON'].notna() & df['CATEGORY OF PERSON'].astype(str).str.strip().str.lower().isin(['promoter group', 'promoters'])]
            cat_f = len(df)
            df = df[df['ACQUISITION/DISPOSAL TRANSACTION TYPE'].notna() & df['ACQUISITION/DISPOSAL TRANSACTION TYPE'].astype(str).str.strip().str.lower().isin(['buy', 'sell'])]
            tra_f = len(df)
            df = df[df['MODE OF ACQUISITION'].notna() & df['MODE OF ACQUISITION'].astype(str).str.strip().str.lower().isin(['market sale', 'market purchase'])]
            mod_f = len(df)
            df = df[df['TYPE OF SECURITY (PRIOR)'].notna() & df['TYPE OF SECURITY (PRIOR)'].astype(str).str.strip().str.lower().str.contains('equity share', na=False)]
            final_count = len(df)
            
            # Clean columns
            to_drop = ['DERIVATIVE TYPE SECURITY', 'DERIVATIVE CONTRACT SPECIFICATION', 'NOTIONAL VALUE(BUY)', 'NUMBER OF UNITS/CONTRACT LOT SIZE (BUY)', 'NOTIONAL VALUE(SELL)', 'NUMBER OF UNITS/CONTRACT LOT SIZE  (SELL)', 'REMARK', 'BROADCASTE DATE AND TIME', 'XBRL', 'TYPE OF SECURITY (ACQUIRED/DISPLOSED)']
            existing_drop = [c for c in to_drop if c in df.columns]
            if existing_drop: df = df.drop(columns=existing_drop)
            
            # Save stats text
            infos = []
            if original_count != reg_f: infos.append(f"{original_count - reg_f} REG '7(3)'")
            if reg_f != cat_f: infos.append(f"{reg_f - cat_f} non-promoter")
            if cat_f != tra_f: infos.append(f"{cat_f - tra_f} non-buy/sell")
            if tra_f != mod_f: infos.append(f"{tra_f - mod_f} non-market")
            if mod_f != final_count: infos.append(f"{mod_f - final_count} non-equity")
            st.session_state.filter_info_text = f"📊 **Filters Applied:** Removed {', '.join(infos)}. Total {final_count} rows." if infos else ""
            
            # 3. Heavy Analytics Logic
            # Prepare transactions_df
            t_df = df.copy()
            numeric_cols = ['NO. OF SECURITIES (ACQUIRED/DISPLOSED)', 'VALUE OF SECURITY (ACQUIRED/DISPLOSED)', '% SHAREHOLDING (PRIOR)', '% POST']
            for col in numeric_cols: t_df[col] = pd.to_numeric(t_df[col], errors='coerce')
            t_df['Shareholding Delta'] = t_df['% POST'] - t_df['% SHAREHOLDING (PRIOR)']
            
            # Grouping
            t_upper = t_df['ACQUISITION/DISPOSAL TRANSACTION TYPE'].astype(str).str.strip().str.upper()
            buy_data = t_df[t_upper == 'BUY']
            sell_data = t_df[t_upper == 'SELL']
            
            def get_sum(data, suffix):
                if len(data) == 0: return pd.DataFrame(columns=['COMPANY', 'SYMBOL', f'Total Share {suffix}s', f'Total Value of Share {suffix}', f'Delta Shareholding {suffix}'])
                res = data.groupby('COMPANY').agg({'SYMBOL': 'first', 'NO. OF SECURITIES (ACQUIRED/DISPLOSED)': 'sum', 'VALUE OF SECURITY (ACQUIRED/DISPLOSED)': 'sum', 'Shareholding Delta': 'sum'}).reset_index()
                res.columns = ['COMPANY', 'SYMBOL', f'Total Share {suffix}s', f'Total Value of Share {suffix}', f'Delta Shareholding {suffix}']
                return res

            b_sum = get_sum(buy_data, 'Buy')
            s_sum = get_sum(sell_data, 'Sell')
            
            # Merge
            comb = pd.merge(b_sum, s_sum.drop(columns=['SYMBOL']), on='COMPANY', how='outer')
            num_cols_all = ['Total Share Buys', 'Total Value of Share Buy', 'Delta Shareholding Buy', 'Total Share Sells', 'Total Value of Share Sell', 'Delta Shareholding Sell']
            for _c in num_cols_all:
                if _c in comb.columns:
                    comb[_c] = pd.to_numeric(comb[_c], errors='coerce').fillna(0)
            if comb['SYMBOL'].isna().any():
                symbol_map = t_df.groupby('COMPANY')['SYMBOL'].first().to_dict()
                comb['SYMBOL'] = comb['COMPANY'].map(symbol_map).fillna(comb['SYMBOL'])
            
            comb = comb[comb['Total Value of Share Buy'] >= 9000000].sort_values('COMPANY').reset_index(drop=True)
            
            # Max Transactions logic
            max_list = []
            for company in t_df['COMPANY'].unique():
                c_buy = buy_data[buy_data['COMPANY'] == company]
                c_sell = sell_data[sell_data['COMPANY'] == company]
                m = {'COMPANY': company}
                
                def get_max_info(c_data, pref):
                    if len(c_data) > 0:
                        v_col, s_col = c_data['VALUE OF SECURITY (ACQUIRED/DISPLOSED)'], c_data['NO. OF SECURITIES (ACQUIRED/DISPLOSED)']
                        idx = v_col.idxmax() if v_col.notna().any() else None
                        m[f'Max {pref} Value'] = c_data.loc[idx, 'VALUE OF SECURITY (ACQUIRED/DISPLOSED)'] if idx else 0
                        
                        max_s = s_col.max()
                        rows_s = c_data[s_col == max_s]
                        if len(rows_s) > 0:
                            val_col = rows_s['VALUE OF SECURITY (ACQUIRED/DISPLOSED)']
                            idx = val_col.idxmax() if val_col.notna().any() else rows_s.index[0]
                            best_row = rows_s.loc[idx]
                            m[f'Number of Max {pref} Shares'] = best_row['NO. OF SECURITIES (ACQUIRED/DISPLOSED)']
                            m[f'Max {pref} Date'] = best_row['DATE OF ALLOTMENT/ACQUISITION FROM']
                    else:
                        m[f'Max {pref} Value'] = 0; m[f'Number of Max {pref} Shares'] = 0; m[f'Max {pref} Date'] = 'N/A'

                get_max_info(c_buy, 'Buy'); get_max_info(c_sell, 'Sell')
                max_list.append(m)
            
            comb = pd.merge(comb, pd.DataFrame(max_list), on='COMPANY', how='left')
            
            # Fundamentals Merge
            f_df = None; s_name = ""
            if fundamentals_file: f_df = pd.read_csv(fundamentals_file); s_name = fundamentals_file.name
            else:
                for p in ["All Name.11-02-2026.Technical.csv", "All Name.17-01-2026.Default.csv"]:
                    if os.path.exists(p): f_df = pd.read_csv(p); s_name = p; break
            
            if f_df is not None:
                f_df['Match_Sym'] = f_df['companyId'].astype(str).str.split(':').str[-1].str.strip()
                comb['Match_Sym'] = comb['SYMBOL'].astype(str).str.strip()
                comb = pd.merge(comb, f_df, left_on='Match_Sym', right_on='Match_Sym', how='left').drop(columns=['Match_Sym'])
            
            # Avgs
            comb['Max Avg Buy'] = (comb['Max Buy Value'] / comb['Number of Max Buy Shares']).fillna(0).round(2)
            comb['Max Avg Sell'] = (comb['Max Sell Value'] / comb['Number of Max Sell Shares']).fillna(0).round(2)
            
            # Column Order
            b_cols = ['Max Buy Date', 'Max Buy Value', 'Number of Max Buy Shares', 'Max Avg Buy', 'Delta Shareholding Buy', 'Total Share Buys', 'Total Value of Share Buy']
            s_cols = ['Max Sell Date', 'Max Sell Value', 'Number of Max Sell Shares', 'Max Avg Sell', 'Delta Shareholding Sell', 'Total Share Sells', 'Total Value of Share Sell']
            other = [c for c in comb.columns if c not in (['COMPANY', 'SYMBOL'] + b_cols + s_cols)]
            order = ['COMPANY', 'SYMBOL'] + [c for c in b_cols if c in comb.columns] + [c for c in s_cols if c in comb.columns] + sorted(other)
            comb = comb[order]
            
            # CSS indices
            st.session_state.buy_max_indices = [i+1 for i, c in enumerate(order) if c in ['Max Buy Date', 'Max Buy Value', 'Number of Max Buy Shares', 'Max Avg Buy']]
            st.session_state.sell_max_indices = [i+1 for i, c in enumerate(order) if c in ['Max Sell Date', 'Max Sell Value', 'Number of Max Sell Shares', 'Max Avg Sell']]
            
            # Commit to state + persist to disk
            st.session_state.df_main = df
            st.session_state.combined_summary = comb
            st.session_state.last_processed_files = current_files
            st.session_state.last_processed_timestamp = datetime.now().strftime("%d %b %Y, %I:%M:%S %p")
            save_cache()
            st.toast("💾 Data cached to disk!", icon="✅")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# --- DISPLAY SECTION ---
if st.session_state.df_main is not None:
    df = st.session_state.df_main
    comb = st.session_state.combined_summary
    
    st.success(f"✅ Data loaded successfully!")
    if st.session_state.filter_info_text: st.info(st.session_state.filter_info_text)
    
    # Overview metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", len(df)); c2.metric("Cols", len(df.columns)); c3.metric("Memory", f"{df.memory_usage().sum()/1024:.1f}KB"); c4.metric("Companies", comb['COMPANY'].nunique() if comb is not None else 0)
    
    # Filters
    st.markdown("---")
    st.subheader("🔽 Data Filters")
    fl, fr = st.columns(2)
    with fl: sel_cols = st.multiselect("Display columns:", df.columns.tolist(), default=df.columns.tolist()[:10])
    with fr: fil_col = st.selectbox("Filter column:", ["None"] + df.columns.tolist())
    
    f_df = df[sel_cols] if sel_cols else df
    if fil_col != "None":
        u_vals = df[fil_col].dropna().unique().tolist()
        if u_vals:
            sv = st.selectbox(f"Value for {fil_col}:", ["All"] + sorted([str(v) for v in u_vals]))
            if sv != "All": f_df = f_df[df[fil_col] == sv]
    
    # Data Table
    st.subheader("📋 Transactions Preview")
    fmt_f = f_df.copy()
    for c in fmt_f.select_dtypes(include=['number']).columns: fmt_f[c] = fmt_f[c].apply(format_indian_number)
    st.dataframe(fmt_f, use_container_width=True, height=350)
    
    # Analytics Table
    if comb is not None:
        st.markdown("---")
        st.subheader("📈 Summary Analytics")
        # CSS
        b_idx, s_idx = st.session_state.buy_max_indices, st.session_state.sell_max_indices
        css_b = f"div[data-testid='stDataFrame'] table thead tr th:nth-child({b_idx[0]}), div[data-testid='stDataFrame'] table tbody tr td:nth-child({b_idx[0]}) {{ border-left: 3px solid #4CAF50 !important; }}" if b_idx else ""
        css_s = f"div[data-testid='stDataFrame'] table thead tr th:nth-child({s_idx[0]}), div[data-testid='stDataFrame'] table tbody tr td:nth-child({s_idx[0]}) {{ border-left: 3px solid #FF9800 !important; }}" if s_idx else ""
        st.markdown(f"<style>{css_b} {css_s}</style>", unsafe_allow_html=True)
        
        fmt_c = comb.copy()
        for c in fmt_c.select_dtypes(include=['number']).columns: fmt_c[c] = fmt_c[c].apply(format_indian_number)
        st.dataframe(fmt_c, use_container_width=True, hide_index=True)
        
        # Download
        csv_b = io.StringIO(); comb.to_csv(csv_b, index=False)
        st.download_button("📥 Download Summary Table", csv_b.getvalue(), "summary.csv", "text/csv")
        
    with st.expander("📊 Data Stats"):
        st.dataframe(df.describe())

else:
    st.info("👆 Please upload a Transactions CSV file to get started.")
    st.markdown("### 📋 Required Columns:")
    st.write(", ".join(REQUIRED_COLUMNS))
