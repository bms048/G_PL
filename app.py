import streamlit as st
import pandas as pd
import datetime
import os
import re

FILE_NAME = 'my_budget_data.xlsx'
COLUMNS = ['תאריך', 'הכנסות', 'הוצאות', 'סיבה להוצאה']

st.set_page_config(page_title="ניהול תקציב חכם", page_icon="💰", layout="centered")

def super_clean_numbers(val):
    """מנקה אגרסיבי: מוחק כל סמל, אות או רווח שאינם מספר, כדי למנוע איפוס ל-0"""
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    
    val_str = str(val)
    # משאיר רק ספרות ונקודה עשרונית
    val_str = re.sub(r'[^\d\.]', '', val_str)
    
    try:
        return float(val_str) if val_str else 0.0
    except ValueError:
        return 0.0

def get_data():
    if os.path.exists(FILE_NAME):
        try:
            df = pd.read_excel(FILE_NAME)
            df.columns = df.columns.str.strip()
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = 0.0 if col in ['הכנסות', 'הוצאות'] else ""
                    
            # הפעלת הניקוי האגרסיבי
            df['הכנסות'] = df['הכנסות'].apply(super_clean_numbers)
            df['הוצאות'] = df['הוצאות'].apply(super_clean_numbers)
            return df
        except Exception:
            return pd.DataFrame(columns=COLUMNS)
    return pd.DataFrame(columns=COLUMNS)

def save_new_entry(entry_data, df):
    new_df = pd.DataFrame([entry_data])
    if df.empty:
        updated_df = new_df
    else:
        updated_df = pd.concat([df, new_df], ignore_index=True)
    
    updated_df['הכנסות'] = updated_df['הכנסות'].apply(super_clean_numbers)
    updated_df['הוצאות'] = updated_df['הוצאות'].apply(super_clean_numbers)
    updated_df.to_excel(FILE_NAME, index=False)
    return updated_df

# --- תחילת האפליקציה ---
df = get_data()

total_income = float(df['הכנסות'].sum()) if not df.empty else 0.0
total_expenses = float(df['הוצאות'].sum()) if not df.empty else 0.0
current_balance = total_income - total_expenses

st.title("ניהול הכנסות והוצאות 💰")

col1, col2, col3 = st.columns(3)
col1.metric(label="יתרה נוכחית", value=f"₪ {current_balance:,.2f}")
col2.metric(label="סה\"כ הכנסות", value=f"₪ {total_income:,.2f}")
col3.metric(label="סה\"כ הוצאות", value=f"₪ {total_expenses:,.2f}")

st.divider()

st.markdown("### הוספת פעולה חדשה")
with st.form(key="transaction_form", clear_on_submit=True):
    transaction_type = st.selectbox("סוג הפעולה:", ["הוצאה", "הכנסה"])
    amount = st.number_input("סכום (₪):", min_value=0.0, step=50.0)
    reason = st.text_input("סיבה (חובה להזין):")
    
    if st.form_submit_button(label="שמור נתונים ועדכן טבלה"):
        if not reason.strip():
            st.error("שגיאה: חובה להזין סיבה כדי לשמור את הפעולה.")
        elif amount <= 0:
            st.error("שגיאה: יש להזין סכום חיובי.")
        else:
            income_val = float(amount) if transaction_type == "הכנסה" else 0.0
            expense_val = float(amount) if transaction_type == "הוצאה" else 0.0
            
            new_entry = {
                'תאריך': datetime.date.today().strftime("%Y-%m-%d"),
                'הכנסות': income_val,
                'הוצאות': expense_val,
                'סיבה להוצאה': reason
            }
            save_new_entry(new_entry, df)
            st.success("הפעולה נשמרה בהצלחה!")
            st.rerun()

st.divider()

with st.expander("🛠️ תפריט אפשרויות מתקדם (היסטוריה וייבוא)"):
    st.markdown("**טבלת הנתונים המלאה:**")
    st.dataframe(df, use_container_width=True)
            
    st.markdown("**העלאת קובץ קודם (ידרוס את הנתונים הקיימים):**")
    uploaded_file = st.file_uploader("בחר קובץ אקסל (.xlsx)", type=['xlsx'])
    
    if uploaded_file is not None:
        if st.button("ייבא והחלף נתונים"):
            try:
                imported_df = pd.read_excel(uploaded_file)
                imported_df.columns = imported_df.columns.str.strip()
                imported_df = imported_df.loc[:, ~imported_df.columns.str.contains('^Unnamed')]
                
                # מפעילים את המנקה האגרסיבי גם ישר על הקובץ שיובא!
                if 'הכנסות' in imported_df.columns:
                    imported_df['הכנסות'] = imported_df['הכנסות'].apply(super_clean_numbers)
                if 'הוצאות' in imported_df.columns:
                    imported_df['הוצאות'] = imported_df['הוצאות'].apply(super_clean_numbers)
                    
                imported_df.to_excel(FILE_NAME, index=False)
                st.success("הקובץ הועלה בהצלחה! מרענן...")
                st.rerun()
            except Exception as e:
                st.error(f"שגיאה בייבוא הקובץ: {e}")
