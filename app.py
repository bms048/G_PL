import streamlit as st
import pandas as pd
import datetime
import re

COLUMNS = ['תאריך', 'הכנסות', 'הוצאות', 'סיבה להוצאה']

st.set_page_config(page_title="ניהול תקציב חכם", page_icon="💰", layout="centered")

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=COLUMNS)

def parse_raw_value(val):
    if pd.isna(val) if isinstance(val, (int, float, str)) else True:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    
    s = str(val).replace('\xa0', '').replace(' ', '').replace(',', '').replace('₪', '').strip()
    try:
        return float(s)
    except ValueError:
        return 0.0

def fix_cols(df):
    rename_map = {}
    for col in df.columns:
        col_clean = str(col).strip()
        if 'הכנס' in col_clean or 'זכות' in col_clean:
            rename_map[col] = 'הכנסות'
        elif 'הוצא' in col_clean or 'חובה' in col_clean:
            rename_map[col] = 'הוצאות'
        elif 'סיבה' in col_clean or 'פירוט' in col_clean or 'תיאור' in col_clean:
            rename_map[col] = 'סיבה להוצאה'
        elif 'תאריך' in col_clean:
            rename_map[col] = 'תאריך'
    return df.rename(columns=rename_map)

# --- חישוב נתונים ---
df = st.session_state.df

income_sum = pd.to_numeric(df['הכנסות'], errors='coerce').fillna(0).sum() if not df.empty and 'הכנסות' in df.columns else 0.0
expense_sum = pd.to_numeric(df['הוצאות'], errors='coerce').fillna(0).sum() if not df.empty and 'הוצאות' in df.columns else 0.0
current_balance = income_sum - expense_sum

st.title("ניהול הכנסות והוצאות 💰")

col1, col2, col3 = st.columns(3)
col1.metric(label="יתרה נוכחית", value=f"₪ {current_balance:,.2f}")
col2.metric(label="סה\"כ הכנסות", value=f"₪ {income_sum:,.2f}")
col3.metric(label="סה\"כ הוצאות", value=f"₪ {expense_sum:,.2f}")

st.divider()

# --- טופס הוספת פעולה ---
st.markdown("### ➕ הוספת פעולה חדשה")
with st.form(key="transaction_form", clear_on_submit=True):
    transaction_type = st.selectbox("סוג הפעולה:", ["הוצאה", "הכנסה"])
    amount = st.number_input("סכום (₪):", min_value=0.0, step=50.0)
    reason = st.text_input("סיבה (חובה להזין):")
    
    if st.form_submit_button(label="שמור פעולה"):
        if not reason.strip():
            st.error("חובה להזין סיבה.")
        elif amount <= 0:
            st.error("חובה להזין סכום חיובי.")
        else:
            income_val = float(amount) if transaction_type == "הכנסה" else 0.0
            expense_val = float(amount) if transaction_type == "הוצאה" else 0.0
            
            new_entry = {
                'תאריך': datetime.date.today().strftime("%Y-%m-%d"),
                'הכנסות': income_val,
                'הוצאות': expense_val,
                'סיבה להוצאה': reason
            }
            new_df = pd.DataFrame([new_entry])
            st.session_state.df = pd.concat([st.session_state.df, new_df], ignore_index=True)
            st.success("הפעולה נוספה בהצלחה!")
            st.rerun()

st.divider()

# --- ייבוא קובץ ---
st.markdown("### 📥 ייבוא קובץ אקסל")
uploaded_file = st.file_uploader("בחר קובץ אקסל (.xlsx):", type=['xlsx'])

if uploaded_file is not None:
    if st.button("טען נתונים מהקובץ"):
        try:
            uploaded_file.seek(0)
            imported_df = pd.read_excel(uploaded_file)
            
            # 1. הסרת עמודות כפולות (השינוי הקריטי!)
            imported_df = imported_df.loc[:, ~imported_df.columns.duplicated()]
            
            # 2. תיקון שמות
            imported_df = fix_cols(imported_df)
            imported_df = imported_df.loc[:, ~imported_df.columns.duplicated()] # שוב למקרה ששני שמות תורגמו לאותו שם
            imported_df = imported_df.loc[:, ~imported_df.columns.str.contains('^Unnamed')]
            
            # 3. מילוי והמרה
            for col in COLUMNS:
                if col not in imported_df.columns:
                    imported_df[col] = 0.0 if col in ['הכנסות', 'הוצאות'] else ""
            
            imported_df['הכנסות'] = pd.to_numeric(imported_df['הכנסות'], errors='coerce').fillna(0)
            imported_df['הוצאות'] = pd.to_numeric(imported_df['הוצאות'], errors='coerce').fillna(0)
            
            st.session_state.df = imported_df[COLUMNS]
            st.success("הנתונים נטענו בהצלחה!")
            st.rerun()
        except Exception as e:
            st.error(f"שגיאה בקריאת הקובץ: {e}")

st.divider()

# --- הצגת הטבלה ---
st.markdown("### 📊 טבלת הנתונים")
st.dataframe(st.session_state.df, use_container_width=True)
