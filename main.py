import streamlit as st
import pandas as pd
import io
import os
import pickle
from datetime import datetime

# ── Helpers ───────────────────────────────────────────────────────────────────
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
            remaining  = integer_part[:-3]
            fmt_rem    = ''
            for i, digit in enumerate(reversed(remaining)):
                if i > 0 and i % 2 == 0:
                    fmt_rem = ',' + fmt_rem
                fmt_rem = digit + fmt_rem
            formatted = fmt_rem + ',' + last_three
        if decimal_part:
            formatted = formatted + '.' + decimal_part
        return ('-' + formatted) if is_negative else formatted
    except (ValueError, TypeError):
        return num

def _css(rules: str):
    """Inject a small CSS snippet safely."""
    st.markdown(f"<style>{rules}</style>", unsafe_allow_html=True)

def _html(content: str):
    """Render raw HTML safely."""
    st.markdown(content, unsafe_allow_html=True)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Promoter Transactions",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Font (Google Fonts via link tag only — no <style> wrapping text) ──────────
_html('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">')

# ── Minimal targeted overrides ────────────────────────────────────────────────
_css("""
html, body, .stApp, [class*="st-"] { font-family: 'Inter', sans-serif !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2.5rem !important; padding-bottom: 2rem !important; }
hr { border-color: #1e2438 !important; margin: 1.25rem 0 !important; }

/* Metric cards */
[data-testid="metric-container"] {
    background: #1a1f2e; border: 1px solid #2a3045;
    border-radius: 12px; padding: .9rem 1.1rem;
    transition: border-color .18s, box-shadow .18s;
}
[data-testid="metric-container"]:hover {
    border-color: #4f86f7; box-shadow: 0 0 0 1px #4f86f7;
}
[data-testid="stMetricLabel"] p {
    font-size: .68rem !important; font-weight: 600 !important;
    text-transform: uppercase; letter-spacing: .08em; color: #6b7a99 !important;
}
[data-testid="stMetricValue"] { font-size: 1.55rem !important; font-weight: 700 !important; }

/* Tables */
[data-testid="stDataFrame"] { border-radius: 10px !important; overflow: hidden; }

/* Download button */
.stDownloadButton > button {
    background: linear-gradient(135deg,#2563eb,#1d4ed8) !important;
    color: #fff !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important;
    font-size: .8rem !important; padding: .45rem 1.1rem !important;
    transition: box-shadow .18s, transform .18s !important;
}
.stDownloadButton > button:hover {
    box-shadow: 0 4px 14px rgba(59,130,246,.45) !important;
    transform: translateY(-1px) !important;
}

/* File uploader — smaller browse button */
[data-testid="stFileUploader"] section button {
    font-size: .73rem !important;
    padding: .3rem .85rem !important;
    border-radius: 7px !important;
}
[data-testid="stFileUploaderDropzone"] {
    padding: .6rem .8rem !important;
}

/* Source badge hover */
.nav-badge {
    display: inline-flex; align-items: center; gap: 6px;
    text-decoration: none; border-radius: 20px;
    font-family: 'Inter', sans-serif; font-size: .73rem; font-weight: 500;
    padding: 5px 12px; border: 1px solid #2a3045;
    transition: border-color .18s, background .18s, box-shadow .18s, transform .18s;
}
.nav-badge:hover {
    border-color: currentColor;
    box-shadow: 0 0 0 1px currentColor;
    transform: translateY(-1px);
    background: #1e2438 !important;
}
.nav-badge-blue  { background: #1a1f2e; color: #93b4f7; }
.nav-badge-purple { background: #1a1f2e; color: #c084fc; }
""")

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
    'BROADCASTE DATE AND TIME', 'XBRL',
]

# ── Page header ───────────────────────────────────────────────────────────────
_html("""
<div style="display:flex;align-items:center;gap:14px;margin-bottom:.75rem;">
  <div style="width:42px;height:42px;border-radius:11px;flex-shrink:0;
              background:linear-gradient(135deg,#2563eb,#7c3aed);
              display:flex;align-items:center;justify-content:center;
              box-shadow:0 4px 14px rgba(37,99,235,.35);">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
         stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
      <polyline points="16 7 22 7 22 13"/>
    </svg>
  </div>
  <div>
    <div style="font-size:1.45rem;font-weight:700;color:#e2e8f7;line-height:1.2;
                font-family:'Inter',sans-serif;">
      Promoter Transactions
    </div>
    <div style="font-size:.73rem;color:#6b7a99;font-family:'Inter',sans-serif;">
      NSE Insider Trading &mdash; Promoter activity tracker &amp; analytics
    </div>
  </div>
</div>
""")

# ── Source badges ─────────────────────────────────────────────────────────────
_html("""
<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px;">
  <a href="https://www.nseindia.com/companies-listing/corporate-filings-insider-trading"
     target="_blank" class="nav-badge nav-badge-blue">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
    </svg>
    NSE India &mdash; Insider Trading
  </a>
  <a href="https://www.stockscans.in/scans" target="_blank"
     class="nav-badge nav-badge-purple">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="3" width="20" height="14" rx="2"/>
      <line x1="8" y1="21" x2="16" y2="21"/>
      <line x1="12" y1="17" x2="12" y2="21"/>
    </svg>
    StockScans &mdash; Screener
  </a>
</div>
<hr/>
""")

# ── Disk cache ────────────────────────────────────────────────────────────────
CACHE_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')
CACHE_FILE = os.path.join(CACHE_DIR, 'app_state.pkl')
CACHE_KEYS = ['df_main', 'combined_summary', 'filter_info_text',
              'last_processed_files', 'buy_max_indices', 'sell_max_indices',
              'last_processed_timestamp']

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'rb') as f:
                saved = pickle.load(f)
            for k in CACHE_KEYS:
                if k not in st.session_state and k in saved:
                    st.session_state[k] = saved[k]
        except Exception:
            pass

def save_cache():
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump({k: st.session_state.get(k) for k in CACHE_KEYS}, f)

load_cache()

if 'df_main'                  not in st.session_state: st.session_state.df_main                  = None
if 'combined_summary'         not in st.session_state: st.session_state.combined_summary         = None
if 'filter_info_text'         not in st.session_state: st.session_state.filter_info_text         = None
if 'last_processed_files'     not in st.session_state: st.session_state.last_processed_files     = (None, None)
if 'buy_max_indices'          not in st.session_state: st.session_state.buy_max_indices          = []
if 'sell_max_indices'         not in st.session_state: st.session_state.sell_max_indices         = []
if 'last_processed_timestamp' not in st.session_state: st.session_state.last_processed_timestamp = None

# ── Upload section ────────────────────────────────────────────────────────────
_html("""
<div style="display:flex;align-items:center;gap:7px;margin-bottom:.6rem;">
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#4f86f7"
       stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
  <span style="font-family:'Inter',sans-serif;font-size:.85rem;font-weight:600;
               color:#c8d4f0;">Data Sources</span>
</div>
""")

col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader(
        "Transactions CSV", type=['csv'],
        help="Upload the primary NSE insider trading CSV file"
    )
with col2:
    fundamentals_file = st.file_uploader(
        "Fundamentals CSV  (optional)", type=['csv'],
        help="Upload a StockScans fundamentals / technical CSV file"
    )

# ── Timestamp badge ───────────────────────────────────────────────────────────
_ts = st.session_state.last_processed_timestamp
if _ts:
    _html(f"""
    <div style="display:inline-flex;align-items:center;gap:6px;margin:4px 0 2px;
                background:#141c2e;border:1px solid #2a3a5e;border-radius:20px;
                padding:4px 12px;">
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#6b93ff"
           stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <polyline points="12 6 12 12 16 14"/>
      </svg>
      <span style="font-family:'Inter',sans-serif;font-size:.7rem;font-weight:600;
                   color:#93b4f7;letter-spacing:.03em;">Last processed: {_ts}</span>
    </div>
    """)

st.markdown("---")

# ── File tracking ─────────────────────────────────────────────────────────────
uploaded_id     = f"{uploaded_file.name}_{uploaded_file.size}"         if uploaded_file     else None
fundamentals_id = f"{fundamentals_file.name}_{fundamentals_file.size}" if fundamentals_file else None
current_files   = (uploaded_id, fundamentals_id)
files_changed   = uploaded_file is not None and current_files != st.session_state.last_processed_files

# ── Processing ────────────────────────────────────────────────────────────────
if files_changed:
    try:
        with st.spinner("Crunching the numbers…"):
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip()
            if not set(REQUIRED_COLUMNS).issubset(set(df.columns)):
                st.error("Missing required columns in uploaded CSV.")
                st.stop()
            df = df[REQUIRED_COLUMNS]
            original_count = len(df)

            df = df[df['REGULATION'].astype(str).str.strip() != '7(3)'];  reg_f = len(df)
            df = df[df['CATEGORY OF PERSON'].notna() & df['CATEGORY OF PERSON'].astype(str).str.strip().str.lower().isin(['promoter group', 'promoters'])]; cat_f = len(df)
            df = df[df['ACQUISITION/DISPOSAL TRANSACTION TYPE'].notna() & df['ACQUISITION/DISPOSAL TRANSACTION TYPE'].astype(str).str.strip().str.lower().isin(['buy', 'sell'])]; tra_f = len(df)
            df = df[df['MODE OF ACQUISITION'].notna() & df['MODE OF ACQUISITION'].astype(str).str.strip().str.lower().isin(['market sale', 'market purchase'])]; mod_f = len(df)
            df = df[df['TYPE OF SECURITY (PRIOR)'].notna() & df['TYPE OF SECURITY (PRIOR)'].astype(str).str.strip().str.lower().str.contains('equity share', na=False)]; final_count = len(df)

            to_drop = ['DERIVATIVE TYPE SECURITY', 'DERIVATIVE CONTRACT SPECIFICATION',
                       'NOTIONAL VALUE(BUY)', 'NUMBER OF UNITS/CONTRACT LOT SIZE (BUY)',
                       'NOTIONAL VALUE(SELL)', 'NUMBER OF UNITS/CONTRACT LOT SIZE  (SELL)',
                       'REMARK', 'BROADCASTE DATE AND TIME', 'XBRL',
                       'TYPE OF SECURITY (ACQUIRED/DISPLOSED)']
            df = df.drop(columns=[c for c in to_drop if c in df.columns])

            infos = []
            if original_count != reg_f:  infos.append(f"{original_count - reg_f} REG 7(3)")
            if reg_f  != cat_f:          infos.append(f"{reg_f  - cat_f}  non-promoter")
            if cat_f  != tra_f:          infos.append(f"{cat_f  - tra_f}  non-buy/sell")
            if tra_f  != mod_f:          infos.append(f"{tra_f  - mod_f}  non-market")
            if mod_f  != final_count:    infos.append(f"{mod_f  - final_count} non-equity")
            st.session_state.filter_info_text = (
                f"Filters removed: {' · '.join(infos)} — {final_count} rows remaining." if infos else ""
            )

            t_df = df.copy()
            for col in ['NO. OF SECURITIES (ACQUIRED/DISPLOSED)',
                        'VALUE OF SECURITY (ACQUIRED/DISPLOSED)',
                        '% SHAREHOLDING (PRIOR)', '% POST']:
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
                    'Shareholding Delta': 'sum',
                }).reset_index()
                res.columns = ['COMPANY', 'SYMBOL',
                               f'Total Share {suffix}s',
                               f'Total Value of Share {suffix}',
                               f'Delta Shareholding {suffix}']
                return res

            b_sum = get_sum(buy_data,  'Buy')
            s_sum = get_sum(sell_data, 'Sell')
            comb  = pd.merge(b_sum, s_sum.drop(columns=['SYMBOL']), on='COMPANY', how='outer')

            for _c in ['Total Share Buys', 'Total Value of Share Buy', 'Delta Shareholding Buy',
                       'Total Share Sells', 'Total Value of Share Sell', 'Delta Shareholding Sell']:
                if _c in comb.columns:
                    comb[_c] = pd.to_numeric(comb[_c], errors='coerce').fillna(0)

            if comb['SYMBOL'].isna().any():
                sym_map = t_df.groupby('COMPANY')['SYMBOL'].first().to_dict()
                comb['SYMBOL'] = comb['COMPANY'].map(sym_map).fillna(comb['SYMBOL'])

            comb = comb[comb['Total Value of Share Buy'] >= 9_000_000].sort_values('COMPANY').reset_index(drop=True)

            max_list = []
            for company in t_df['COMPANY'].unique():
                c_buy  = buy_data[buy_data['COMPANY']  == company]
                c_sell = sell_data[sell_data['COMPANY'] == company]
                m = {'COMPANY': company}

                def get_max_info(c_data, pref):
                    if len(c_data) > 0:
                        v_col = c_data['VALUE OF SECURITY (ACQUIRED/DISPLOSED)']
                        s_col = c_data['NO. OF SECURITIES (ACQUIRED/DISPLOSED)']
                        idx   = v_col.idxmax() if v_col.notna().any() else None
                        m[f'Max {pref} Value'] = c_data.loc[idx, 'VALUE OF SECURITY (ACQUIRED/DISPLOSED)'] if idx is not None else 0
                        rows_s = c_data[s_col == s_col.max()]
                        if len(rows_s) > 0:
                            vc  = rows_s['VALUE OF SECURITY (ACQUIRED/DISPLOSED)']
                            i2  = vc.idxmax() if vc.notna().any() else rows_s.index[0]
                            br  = rows_s.loc[i2]
                            m[f'Number of Max {pref} Shares'] = br['NO. OF SECURITIES (ACQUIRED/DISPLOSED)']
                            m[f'Max {pref} Date']             = br['DATE OF ALLOTMENT/ACQUISITION FROM']
                    else:
                        m[f'Max {pref} Value'] = 0; m[f'Number of Max {pref} Shares'] = 0; m[f'Max {pref} Date'] = 'N/A'

                get_max_info(c_buy, 'Buy'); get_max_info(c_sell, 'Sell')
                max_list.append(m)

            comb = pd.merge(comb, pd.DataFrame(max_list), on='COMPANY', how='left')

            f_df = None
            if fundamentals_file:
                f_df = pd.read_csv(fundamentals_file)
            else:
                for p in ["All Name.11-02-2026.Technical.csv", "All Name.17-01-2026.Default.csv"]:
                    if os.path.exists(p):
                        f_df = pd.read_csv(p); break
            if f_df is not None:
                f_df['Match_Sym']  = f_df['companyId'].astype(str).str.split(':').str[-1].str.strip()
                comb['Match_Sym']  = comb['SYMBOL'].astype(str).str.strip()
                comb = pd.merge(comb, f_df, left_on='Match_Sym', right_on='Match_Sym', how='left').drop(columns=['Match_Sym'])

            comb['Max Avg Buy']  = (comb['Max Buy Value']  / comb['Number of Max Buy Shares']).fillna(0).round(2)
            comb['Max Avg Sell'] = (comb['Max Sell Value'] / comb['Number of Max Sell Shares']).fillna(0).round(2)

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

            st.session_state.df_main                  = df
            st.session_state.combined_summary         = comb
            st.session_state.last_processed_files     = current_files
            st.session_state.last_processed_timestamp = datetime.now().strftime("%d %b %Y, %I:%M:%S %p")
            save_cache()
            st.toast("Data processed and cached.", icon="✅")

    except Exception as e:
        st.error(f"Error: {e}")

# ── Display ───────────────────────────────────────────────────────────────────
if st.session_state.df_main is not None:
    df   = st.session_state.df_main
    comb = st.session_state.combined_summary

    ft = st.session_state.filter_info_text
    if ft:
        _html(f"""
        <div style="background:#141c2e;border:1px solid #2a3a5e;border-radius:10px;
                    padding:9px 15px;margin-bottom:.8rem;display:flex;
                    align-items:center;gap:8px;">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#4f86f7"
               stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
          </svg>
          <span style="font-family:'Inter',sans-serif;font-size:.75rem;color:#7a9fd4;">{ft}</span>
        </div>
        """)

    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Transactions", f"{len(df):,}")
    c2.metric("Columns",       len(df.columns))
    c3.metric("Memory",        f"{df.memory_usage().sum()/1024:.1f} KB")
    c4.metric("Companies",     comb['COMPANY'].nunique() if comb is not None else 0)

    st.markdown("---")

    # Filters
    _html("""
    <div style="display:flex;align-items:center;gap:7px;margin-bottom:.5rem;">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#4f86f7"
           stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
      </svg>
      <span style="font-family:'Inter',sans-serif;font-size:.85rem;
                   font-weight:600;color:#c8d4f0;">Filter &amp; Explore</span>
    </div>
    """)

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

    # Transactions table
    _html("""
    <div style="display:flex;align-items:center;gap:7px;margin:1rem 0 .4rem;">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#6b93d6"
           stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2"/>
        <line x1="3" y1="9" x2="21" y2="9"/>
        <line x1="3" y1="15" x2="21" y2="15"/>
        <line x1="9" y1="3" x2="9" y2="21"/>
      </svg>
      <span style="font-family:'Inter',sans-serif;font-size:.85rem;
                   font-weight:600;color:#c8d4f0;">Transaction Records</span>
    </div>
    """)

    fmt_f = f_df.copy()
    for c in fmt_f.select_dtypes(include=['number']).columns:
        fmt_f[c] = fmt_f[c].apply(format_indian_number)
    st.dataframe(fmt_f, use_container_width=True, height=340)

    # Analytics table
    if comb is not None:
        st.markdown("---")
        _html("""
        <div style="display:flex;align-items:center;gap:7px;margin-bottom:.4rem;flex-wrap:wrap;">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#6b93d6"
               stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="20" x2="18" y2="10"/>
            <line x1="12" y1="20" x2="12" y2="4"/>
            <line x1="6"  y1="20" x2="6"  y2="14"/>
          </svg>
          <span style="font-family:'Inter',sans-serif;font-size:.85rem;
                       font-weight:600;color:#c8d4f0;">Summary Analytics</span>
          <span style="font-family:'Inter',sans-serif;font-size:.67rem;color:#6b7a99;
                       background:#1a1f2e;border:1px solid #2a3045;border-radius:20px;
                       padding:2px 9px;font-weight:500;">Buy &ge; &#8377;90 L</span>
        </div>
        """)

        b_idx = st.session_state.buy_max_indices
        s_idx = st.session_state.sell_max_indices
        if b_idx:
            _css(f"[data-testid='stDataFrame'] table thead tr th:nth-child({b_idx[0]}),"
                 f"[data-testid='stDataFrame'] table tbody tr td:nth-child({b_idx[0]})"
                 f"{{border-left:2px solid #22c55e !important;}}")
        if s_idx:
            _css(f"[data-testid='stDataFrame'] table thead tr th:nth-child({s_idx[0]}),"
                 f"[data-testid='stDataFrame'] table tbody tr td:nth-child({s_idx[0]})"
                 f"{{border-left:2px solid #f59e0b !important;}}")

        fmt_c = comb.copy()
        for c in fmt_c.select_dtypes(include=['number']).columns:
            fmt_c[c] = fmt_c[c].apply(format_indian_number)
        st.dataframe(fmt_c, use_container_width=True, hide_index=True)

        col_dl, _ = st.columns([1, 4])
        with col_dl:
            buf = io.StringIO()
            comb.to_csv(buf, index=False)
            st.download_button("Download Summary CSV", buf.getvalue(),
                               "promoter_summary.csv", "text/csv")

    with st.expander("Data Statistics"):
        st.dataframe(df.describe(), use_container_width=True)

else:
    _html("""
    <div style="text-align:center;padding:3rem 1rem;background:#1a1f2e;
                border:1.5px dashed #2a3045;border-radius:14px;margin-top:1rem;">
      <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#2a3a5e"
           stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
           style="margin-bottom:.8rem;">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="17 8 12 3 7 8"/>
        <line x1="12" y1="3" x2="12" y2="15"/>
      </svg>
      <p style="font-family:'Inter',sans-serif;font-size:.95rem;font-weight:600;
                color:#3a4a64;margin:0 0 5px;">No data loaded</p>
      <p style="font-family:'Inter',sans-serif;font-size:.78rem;color:#2a3a54;margin:0;">
        Upload a Transactions CSV file above to get started
      </p>
    </div>
    """)
