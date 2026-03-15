import streamlit as st
import pandas as pd
import io
import os
import pickle
from datetime import datetime

# ── Helpers ──────────────────────────────────────────────────────────────────
def format_indian_number(num):
    if pd.isna(num):
        return num
    try:
        num = float(num)
        if num == 0:
            return "0"
        is_negative = num < 0
        num = abs(num)
        num_str = f"{num:.2f}"
        integer_part, decimal_part = num_str.split('.')
        decimal_part = decimal_part.rstrip('0').rstrip('.')
        if len(integer_part) <= 3:
            formatted = integer_part
        else:
            last_three = integer_part[-3:]
            remaining = integer_part[:-3]
            formatted_remaining = ''
            for i, digit in enumerate(reversed(remaining)):
                if i > 0 and i % 2 == 0:
                    formatted_remaining = ',' + formatted_remaining
                formatted_remaining = digit + formatted_remaining
            formatted = formatted_remaining + ',' + last_three
        if decimal_part:
            formatted = formatted + '.' + decimal_part
        if is_negative:
            formatted = '-' + formatted
        return formatted
    except (ValueError, TypeError):
        return num

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Promoter Transactions",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Required columns ──────────────────────────────────────────────────────────
REQUIRED_COLUMNS = [
    'SYMBOL', 'COMPANY', 'REGULATION', 'NAME OF THE ACQUIRER/DISPOSER',
    'CATEGORY OF PERSON', 'TYPE OF SECURITY (PRIOR)', 'NO. OF SECURITY (PRIOR)',
    '% SHAREHOLDING (PRIOR)', 'TYPE OF SECURITY (ACQUIRED/DISPLOSED)',
    'NO. OF SECURITIES (ACQUIRED/DISPLOSED)', 'VALUE OF SECURITY (ACQUIRED/DISPLOSED)',
    'ACQUISITION/DISPOSAL TRANSACTION TYPE', 'TYPE OF SECURITY (POST)',
    'NO. OF SECURITY (POST)', '% POST', 'DATE OF ALLOTMENT/ACQUISITION FROM',
    'DATE OF ALLOTMENT/ACQUISITION TO', 'DATE OF INITMATION TO COMPANY',
    'MODE OF ACQUISITION', 'DERIVATIVE TYPE SECURITY',
    'DERIVATIVE CONTRACT SPECIFICATION', 'NOTIONAL VALUE(BUY)',
    'NUMBER OF UNITS/CONTRACT LOT SIZE (BUY)', 'NOTIONAL VALUE(SELL)',
    'NUMBER OF UNITS/CONTRACT LOT SIZE  (SELL)', 'EXCHANGE', 'REMARK',
    'BROADCASTE DATE AND TIME', 'XBRL'
]

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>

/* ── Base typography ── */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1a1f2e 0%, #141824 100%);
    border: 1px solid #2a3045;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    transition: border-color .2s, transform .2s;
}
[data-testid="metric-container"]:hover {
    border-color: #4f86f7;
    transform: translateY(-2px);
}
[data-testid="stMetricLabel"] {
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #6b7a99 !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: #e2e8f7 !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #2a3045 !important;
    border-radius: 10px !important;
    overflow: hidden;
}
[data-testid="stDataFrame"] table {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.8rem !important;
}
[data-testid="stDataFrame"] thead th {
    background: #1a1f2e !important;
    color: #8b9bb4 !important;
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    border-bottom: 1px solid #2a3045 !important;
}
[data-testid="stDataFrame"] tbody tr:hover td {
    background: #1e2438 !important;
}

/* ── Upload area ── */
[data-testid="stFileUploader"] {
    background: #141824;
    border: 1.5px dashed #2a3045;
    border-radius: 12px;
    padding: 0.5rem;
    transition: border-color .2s;
}
[data-testid="stFileUploader"]:hover {
    border-color: #4f86f7;
}
[data-testid="stFileUploader"] label {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    color: #8b9bb4 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ── Buttons ── */
.stDownloadButton > button, .stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.2rem !important;
    transition: all .2s !important;
}
.stDownloadButton > button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    color: white !important;
    border: none !important;
}
.stDownloadButton > button:hover {
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    box-shadow: 0 4px 14px rgba(59,130,246,.4) !important;
    transform: translateY(-1px) !important;
}

/* ── Selectbox / Multiselect ── */
[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label {
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    color: #6b7a99 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    border: 1px solid #2a3045 !important;
    border-radius: 10px !important;
    background: #141824 !important;
}

/* ── Divider ── */
hr { border-color: #1e2438 !important; margin: 1.5rem 0 !important; }

/* ── Spinner ── */
[data-testid="stSpinner"] p {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    color: #6b7a99 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:0.5rem;">
    <div style="display:flex;align-items:center;gap:14px;">
        <div style="
            width:44px;height:44px;border-radius:12px;
            background:linear-gradient(135deg,#2563eb,#7c3aed);
            display:flex;align-items:center;justify-content:center;
            box-shadow:0 4px 14px rgba(37,99,235,.35);
            flex-shrink:0;
        ">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline>
                <polyline points="16 7 22 7 22 13"></polyline>
            </svg>
        </div>
        <div>
            <h1 style="margin:0;font-family:'Inter',sans-serif;font-size:1.55rem;font-weight:700;color:#e2e8f7;line-height:1.2;">
                Promoter Transactions
            </h1>
            <p style="margin:0;font-size:0.75rem;color:#6b7a99;font-weight:400;letter-spacing:0.02em;">
                NSE Insider Trading — Promoter activity tracker &amp; analytics
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Source badges ─────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 18px 0;">
    <a href="https://www.nseindia.com/companies-listing/corporate-filings-insider-trading"
       target="_blank"
       style="display:inline-flex;align-items:center;gap:6px;text-decoration:none;
              background:#1a1f2e;border:1px solid #2a3045;color:#93b4f7;
              font-family:'Inter',sans-serif;font-size:0.75rem;font-weight:500;
              padding:5px 12px;border-radius:20px;transition:all .2s;"
       onmouseover="this.style.borderColor='#4f86f7';this.style.background='#1e2a45';"
       onmouseout="this.style.borderColor='#2a3045';this.style.background='#1a1f2e';">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
        </svg>
        NSE India — Insider Trading
    </a>
    <a href="https://www.stockscans.in/scans"
       target="_blank"
       style="display:inline-flex;align-items:center;gap:6px;text-decoration:none;
              background:#1a1f2e;border:1px solid #2a3045;color:#c084fc;
              font-family:'Inter',sans-serif;font-size:0.75rem;font-weight:500;
              padding:5px 12px;border-radius:20px;transition:all .2s;"
       onmouseover="this.style.borderColor='#9333ea';this.style.background='#1f1a2e';"
       onmouseout="this.style.borderColor='#2a3045';this.style.background='#1a1f2e';">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
            <line x1="8" y1="21" x2="16" y2="21"></line>
            <line x1="12" y1="17" x2="12" y2="21"></line>
        </svg>
        StockScans — Screener
    </a>
</div>
<hr>
""", unsafe_allow_html=True)

# ── Disk cache helpers ────────────────────────────────────────────────────────
CACHE_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')
CACHE_FILE = os.path.join(CACHE_DIR, 'app_state.pkl')

CAKEY_KEYS = ['df_main', 'combined_summary', 'filter_info_text',
               'last_processed_files', 'buy_max_indices', 'sell_max_indices',
               'last_processed_timestamp']

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'rb') as f:
                saved = pickle.load(f)
            for k in CAKEY_KEYS:
                if k not in st.session_state and k in saved:
                    st.session_state[k] = saved[k]
        except Exception:
            pass

def save_cache():
    os.makedirs(CACHE_DIR, exist_ok=True)
    payload = {k: st.session_state.get(k) for k in CAKEY_KEYS}
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(payload, f)

load_cache()

# ── Session state defaults ────────────────────────────────────────────────────
if 'df_main'               not in st.session_state: st.session_state.df_main               = None
if 'combined_summary'      not in st.session_state: st.session_state.combined_summary      = None
if 'filter_info_text'      not in st.session_state: st.session_state.filter_info_text      = None
if 'last_processed_files'  not in st.session_state: st.session_state.last_processed_files  = (None, None)
if 'buy_max_indices'       not in st.session_state: st.session_state.buy_max_indices       = []
if 'sell_max_indices'      not in st.session_state: st.session_state.sell_max_indices      = []
if 'last_processed_timestamp' not in st.session_state: st.session_state.last_processed_timestamp = None

# ── Upload section header ─────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;gap:8px;margin-bottom:0.75rem;">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#4f86f7"
         stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="17 8 12 3 7 8"></polyline>
        <line x1="12" y1="3" x2="12" y2="15"></line>
    </svg>
    <span style="font-family:'Inter',sans-serif;font-size:0.9rem;font-weight:600;
                 color:#c8d4f0;letter-spacing:0.01em;">Data Sources</span>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader(
        "Transactions CSV", type=['csv'],
        help="Upload the primary NSE insider trading CSV file"
    )
with col2:
    fundamentals_file = st.file_uploader(
        "Fundamentals CSV  ·  optional", type=['csv'],
        help="Upload a StockScans fundamentals/technical CSV file"
    )

# ── Timestamp badge ───────────────────────────────────────────────────────────
_ts = st.session_state.last_processed_timestamp
if _ts:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:8px;margin:6px 0 4px 2px;flex-wrap:wrap;">
        <span style="font-family:'Inter',sans-serif;font-size:0.72rem;
                     color:#6b7a99;font-weight:500;letter-spacing:0.04em;">
            LAST PROCESSED
        </span>
        <span style="
            display:inline-flex;align-items:center;gap:5px;
            background:#141c2e;color:#93b4f7;
            font-family:'Inter',sans-serif;font-size:0.72rem;font-weight:600;
            padding:3px 10px;border-radius:20px;
            border:1px solid #2a3a5e;letter-spacing:0.03em;">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            {_ts}
        </span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── File tracking ─────────────────────────────────────────────────────────────
uploaded_id     = f"{uploaded_file.name}_{uploaded_file.size}"      if uploaded_file     else None
fundamentals_id = f"{fundamentals_file.name}_{fundamentals_file.size}" if fundamentals_file else None
current_files   = (uploaded_id, fundamentals_id)
files_changed   = uploaded_file is not None and current_files != st.session_state.last_processed_files

# ── Processing ────────────────────────────────────────────────────────────────
if files_changed:
    try:
        with st.spinner("Crunching the numbers…"):
            # 1. Read & clean
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip()
            if not set(REQUIRED_COLUMNS).issubset(set(df.columns)):
                st.error("Missing required columns in uploaded CSV.")
                st.stop()
            df = df[REQUIRED_COLUMNS]
            original_count = len(df)

            # 2. Filters
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

            # Drop derivative/noise columns
            to_drop = ['DERIVATIVE TYPE SECURITY', 'DERIVATIVE CONTRACT SPECIFICATION',
                       'NOTIONAL VALUE(BUY)', 'NUMBER OF UNITS/CONTRACT LOT SIZE (BUY)',
                       'NOTIONAL VALUE(SELL)', 'NUMBER OF UNITS/CONTRACT LOT SIZE  (SELL)',
                       'REMARK', 'BROADCASTE DATE AND TIME', 'XBRL',
                       'TYPE OF SECURITY (ACQUIRED/DISPLOSED)']
            df = df.drop(columns=[c for c in to_drop if c in df.columns])

            # Filter stats
            infos = []
            if original_count != reg_f:   infos.append(f"{original_count - reg_f} REG 7(3)")
            if reg_f != cat_f:            infos.append(f"{reg_f - cat_f} non-promoter")
            if cat_f != tra_f:            infos.append(f"{cat_f - tra_f} non-buy/sell")
            if tra_f != mod_f:            infos.append(f"{tra_f - mod_f} non-market")
            if mod_f != final_count:      infos.append(f"{mod_f - final_count} non-equity")
            st.session_state.filter_info_text = (
                f"Filters removed: {' · '.join(infos)} — {final_count} rows remaining." if infos else ""
            )

            # 3. Analytics
            t_df = df.copy()
            numeric_cols = ['NO. OF SECURITIES (ACQUIRED/DISPLOSED)',
                            'VALUE OF SECURITY (ACQUIRED/DISPLOSED)',
                            '% SHAREHOLDING (PRIOR)', '% POST']
            for col in numeric_cols:
                t_df[col] = pd.to_numeric(t_df[col], errors='coerce')
            t_df['Shareholding Delta'] = t_df['% POST'] - t_df['% SHAREHOLDING (PRIOR)']

            t_upper   = t_df['ACQUISITION/DISPOSAL TRANSACTION TYPE'].astype(str).str.strip().str.upper()
            buy_data  = t_df[t_upper == 'BUY']
            sell_data = t_df[t_upper == 'SELL']

            def get_sum(data, suffix):
                if len(data) == 0:
                    return pd.DataFrame(columns=['COMPANY', 'SYMBOL',
                        f'Total Share {suffix}s', f'Total Value of Share {suffix}',
                        f'Delta Shareholding {suffix}'])
                res = data.groupby('COMPANY').agg({
                    'SYMBOL': 'first',
                    'NO. OF SECURITIES (ACQUIRED/DISPLOSED)': 'sum',
                    'VALUE OF SECURITY (ACQUIRED/DISPLOSED)': 'sum',
                    'Shareholding Delta': 'sum'
                }).reset_index()
                res.columns = ['COMPANY', 'SYMBOL',
                               f'Total Share {suffix}s',
                               f'Total Value of Share {suffix}',
                               f'Delta Shareholding {suffix}']
                return res

            b_sum = get_sum(buy_data, 'Buy')
            s_sum = get_sum(sell_data, 'Sell')

            comb = pd.merge(b_sum, s_sum.drop(columns=['SYMBOL']), on='COMPANY', how='outer')
            num_cols_all = ['Total Share Buys', 'Total Value of Share Buy', 'Delta Shareholding Buy',
                            'Total Share Sells', 'Total Value of Share Sell', 'Delta Shareholding Sell']
            for _c in num_cols_all:
                if _c in comb.columns:
                    comb[_c] = pd.to_numeric(comb[_c], errors='coerce').fillna(0)

            if comb['SYMBOL'].isna().any():
                symbol_map = t_df.groupby('COMPANY')['SYMBOL'].first().to_dict()
                comb['SYMBOL'] = comb['COMPANY'].map(symbol_map).fillna(comb['SYMBOL'])

            comb = comb[comb['Total Value of Share Buy'] >= 9_000_000].sort_values('COMPANY').reset_index(drop=True)

            # Max transactions
            max_list = []
            for company in t_df['COMPANY'].unique():
                c_buy  = buy_data[buy_data['COMPANY'] == company]
                c_sell = sell_data[sell_data['COMPANY'] == company]
                m = {'COMPANY': company}

                def get_max_info(c_data, pref):
                    if len(c_data) > 0:
                        v_col = c_data['VALUE OF SECURITY (ACQUIRED/DISPLOSED)']
                        s_col = c_data['NO. OF SECURITIES (ACQUIRED/DISPLOSED)']
                        idx = v_col.idxmax() if v_col.notna().any() else None
                        m[f'Max {pref} Value'] = c_data.loc[idx, 'VALUE OF SECURITY (ACQUIRED/DISPLOSED)'] if idx is not None else 0
                        max_s  = s_col.max()
                        rows_s = c_data[s_col == max_s]
                        if len(rows_s) > 0:
                            val_col = rows_s['VALUE OF SECURITY (ACQUIRED/DISPLOSED)']
                            idx2    = val_col.idxmax() if val_col.notna().any() else rows_s.index[0]
                            best    = rows_s.loc[idx2]
                            m[f'Number of Max {pref} Shares'] = best['NO. OF SECURITIES (ACQUIRED/DISPLOSED)']
                            m[f'Max {pref} Date']             = best['DATE OF ALLOTMENT/ACQUISITION FROM']
                    else:
                        m[f'Max {pref} Value'] = 0
                        m[f'Number of Max {pref} Shares'] = 0
                        m[f'Max {pref} Date'] = 'N/A'

                get_max_info(c_buy, 'Buy')
                get_max_info(c_sell, 'Sell')
                max_list.append(m)

            comb = pd.merge(comb, pd.DataFrame(max_list), on='COMPANY', how='left')

            # Fundamentals merge
            f_df = None
            if fundamentals_file:
                f_df = pd.read_csv(fundamentals_file)
            else:
                for p in ["All Name.11-02-2026.Technical.csv", "All Name.17-01-2026.Default.csv"]:
                    if os.path.exists(p):
                        f_df = pd.read_csv(p)
                        break
            if f_df is not None:
                f_df['Match_Sym'] = f_df['companyId'].astype(str).str.split(':').str[-1].str.strip()
                comb['Match_Sym'] = comb['SYMBOL'].astype(str).str.strip()
                comb = pd.merge(comb, f_df, left_on='Match_Sym', right_on='Match_Sym', how='left').drop(columns=['Match_Sym'])

            # Averages
            comb['Max Avg Buy']  = (comb['Max Buy Value']  / comb['Number of Max Buy Shares']).fillna(0).round(2)
            comb['Max Avg Sell'] = (comb['Max Sell Value'] / comb['Number of Max Sell Shares']).fillna(0).round(2)

            # Column ordering
            b_cols = ['Max Buy Date', 'Max Buy Value', 'Number of Max Buy Shares', 'Max Avg Buy',
                      'Delta Shareholding Buy', 'Total Share Buys', 'Total Value of Share Buy']
            s_cols = ['Max Sell Date', 'Max Sell Value', 'Number of Max Sell Shares', 'Max Avg Sell',
                      'Delta Shareholding Sell', 'Total Share Sells', 'Total Value of Share Sell']
            other = [c for c in comb.columns if c not in (['COMPANY', 'SYMBOL'] + b_cols + s_cols)]
            order = (['COMPANY', 'SYMBOL']
                     + [c for c in b_cols if c in comb.columns]
                     + [c for c in s_cols if c in comb.columns]
                     + sorted(other))
            comb = comb[order]

            st.session_state.buy_max_indices  = [i+1 for i, c in enumerate(order) if c in ['Max Buy Date', 'Max Buy Value', 'Number of Max Buy Shares', 'Max Avg Buy']]
            st.session_state.sell_max_indices = [i+1 for i, c in enumerate(order) if c in ['Max Sell Date', 'Max Sell Value', 'Number of Max Sell Shares', 'Max Avg Sell']]

            # Commit & persist
            st.session_state.df_main               = df
            st.session_state.combined_summary      = comb
            st.session_state.last_processed_files  = current_files
            st.session_state.last_processed_timestamp = datetime.now().strftime("%d %b %Y, %I:%M:%S %p")
            save_cache()
            st.toast("Data processed and cached.", icon="✅")

    except Exception as e:
        st.error(f"Error: {str(e)}")

# ── Display section ───────────────────────────────────────────────────────────
if st.session_state.df_main is not None:
    df   = st.session_state.df_main
    comb = st.session_state.combined_summary

    # Status bar
    ft = st.session_state.filter_info_text
    if ft:
        st.markdown(f"""
        <div style="
            background:#141c2e;border:1px solid #2a3a5e;border-radius:10px;
            padding:10px 16px;margin-bottom:1rem;
            font-family:'Inter',sans-serif;font-size:0.78rem;color:#7a9fd4;
            display:flex;align-items:center;gap:8px;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#4f86f7"
                 stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
            </svg>
            {ft}
        </div>
        """, unsafe_allow_html=True)

    # ── Metric cards ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Transactions",  f"{len(df):,}")
    c2.metric("Columns",       len(df.columns))
    c3.metric("Memory",        f"{df.memory_usage().sum()/1024:.1f} KB")
    c4.metric("Companies",     comb['COMPANY'].nunique() if comb is not None else 0)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Filters ───────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:0.6rem;">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#4f86f7"
             stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
        </svg>
        <span style="font-family:'Inter',sans-serif;font-size:0.9rem;font-weight:600;
                     color:#c8d4f0;">Filter & Explore</span>
    </div>
    """, unsafe_allow_html=True)

    fl, fr = st.columns(2)
    with fl:
        sel_cols = st.multiselect("Display columns", df.columns.tolist(), default=df.columns.tolist()[:10])
    with fr:
        fil_col = st.selectbox("Filter by column", ["None"] + df.columns.tolist())

    f_df = df[sel_cols] if sel_cols else df
    if fil_col != "None":
        u_vals = df[fil_col].dropna().unique().tolist()
        if u_vals:
            sv = st.selectbox(f"Value — {fil_col}", ["All"] + sorted([str(v) for v in u_vals]))
            if sv != "All":
                f_df = f_df[df[fil_col] == sv]

    # ── Transactions table ────────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.5rem 0;">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#6b93d6"
             stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="3" y1="9" x2="21" y2="9"></line>
            <line x1="3" y1="15" x2="21" y2="15"></line>
            <line x1="9" y1="3" x2="9" y2="21"></line>
        </svg>
        <span style="font-family:'Inter',sans-serif;font-size:0.9rem;font-weight:600;
                     color:#c8d4f0;">Transaction Records</span>
    </div>
    """, unsafe_allow_html=True)

    fmt_f = f_df.copy()
    for c in fmt_f.select_dtypes(include=['number']).columns:
        fmt_f[c] = fmt_f[c].apply(format_indian_number)
    st.dataframe(fmt_f, use_container_width=True, height=340)

    # ── Summary analytics ─────────────────────────────────────────────────────
    if comb is not None:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:0.5rem;">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#6b93d6"
                 stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="20" x2="18" y2="10"></line>
                <line x1="12" y1="20" x2="12" y2="4"></line>
                <line x1="6"  y1="20" x2="6"  y2="14"></line>
            </svg>
            <span style="font-family:'Inter',sans-serif;font-size:0.9rem;font-weight:600;
                         color:#c8d4f0;">Summary Analytics</span>
            <span style="font-family:'Inter',sans-serif;font-size:0.7rem;color:#6b7a99;
                         background:#1a1f2e;border:1px solid #2a3045;border-radius:20px;
                         padding:2px 9px;font-weight:500;">
                Buy ≥ ₹90 L filter applied
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Column-border CSS for buy/sell split
        b_idx = st.session_state.buy_max_indices
        s_idx = st.session_state.sell_max_indices
        css_b = (f"div[data-testid='stDataFrame'] table thead tr th:nth-child({b_idx[0]}),"
                 f"div[data-testid='stDataFrame'] table tbody tr td:nth-child({b_idx[0]})"
                 f"{{ border-left: 2px solid #22c55e !important; }}") if b_idx else ""
        css_s = (f"div[data-testid='stDataFrame'] table thead tr th:nth-child({s_idx[0]}),"
                 f"div[data-testid='stDataFrame'] table tbody tr td:nth-child({s_idx[0]})"
                 f"{{ border-left: 2px solid #f59e0b !important; }}") if s_idx else ""
        st.markdown(f"<style>{css_b} {css_s}</style>", unsafe_allow_html=True)

        fmt_c = comb.copy()
        for c in fmt_c.select_dtypes(include=['number']).columns:
            fmt_c[c] = fmt_c[c].apply(format_indian_number)
        st.dataframe(fmt_c, use_container_width=True, hide_index=True)

        col_dl, _ = st.columns([1, 5])
        with col_dl:
            csv_b = io.StringIO()
            comb.to_csv(csv_b, index=False)
            st.download_button(
                label="Download Summary CSV",
                data=csv_b.getvalue(),
                file_name="promoter_summary.csv",
                mime="text/csv",
            )

    with st.expander("Data Statistics"):
        st.dataframe(df.describe(), use_container_width=True)

else:
    # ── Empty state ───────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        text-align:center;padding:3rem 1rem;
        background:#141824;border:1.5px dashed #2a3045;
        border-radius:16px;margin-top:1rem;">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#2a3a5e"
             stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
             style="margin-bottom:1rem;">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
        </svg>
        <p style="font-family:'Inter',sans-serif;font-size:1rem;font-weight:600;
                  color:#4a5568;margin:0 0 6px 0;">No data loaded</p>
        <p style="font-family:'Inter',sans-serif;font-size:0.8rem;color:#3a4558;margin:0;">
            Upload a Transactions CSV file above to get started
        </p>
    </div>
    """, unsafe_allow_html=True)
