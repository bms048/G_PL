import streamlit as st
import pandas as pd
import datetime
import os

# --- הגדרות בסיסיות ---
FILE_NAME = 'my_budget_data.xlsx'
COLUMNS = ['תאריך', 'הכנסות', 'הוצאות', 'סיבה להוצאה']

st.set_page_config(page_title="ניהול תקציב חכם", page_icon="💰", layout="centered")

def get_data():
    """טעינת נתונים עם הגנה מפני קריסות (רווחים בכותרות או קבצים ריקים)."""
    if os.path.exists(FILE_NAME):
        try:
            df = pd.read_excel(FILE_NAME)
            # ניקוי רווחים נסתרים משמות העמודות
            df.columns = df.columns.str.strip()
            # --- זו השורה החדשה שאתה צריך להוסיף: מוחק עמודות Unnamed ---
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            # וידוא שכל העמודות הקריטיות קיימות
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = 0.0 if col in ['הכנסות', 'הוצאות'] else ""
                    
            return df
        except Exception:
            return pd.DataFrame(columns=COLUMNS)
            
    return pd.DataFrame(columns=COLUMNS)

def save_new_entry(entry_data, df):
    """שמירת שורה חדשה לאקסל בצורה בטוחה."""
    new_df = pd.DataFrame([entry_data])
    if df.empty:
        updated_df = new_df
    else:
        updated_df = pd.concat([df, new_df], ignore_index=True)
    
    # המרה לערכים מספריים לפני השמירה כדי למנוע שגיאות חישוב
    updated_df['הכנסות'] = pd.to_numeric(updated_df['הכנסות'], errors='coerce').fillna(0)
    updated_df['הוצאות'] = pd.to_numeric(updated_df['הוצאות'], errors='coerce').fillna(0)
    
    updated_df.to_excel(FILE_NAME, index=False)
    return updated_df

# קריאת הנתונים מהקובץ
df = get_data()

# חישוב הסכומים להצגה למעלה
total_income = float(df['הכנסות'].sum()) if not df.empty else 0.0
total_expenses = float(df['הוצאות'].sum()) if not df.empty else 0.0
current_balance = total_income - total_expenses

# --- ממשק המשתמש: כותרת ונתונים ---
st.title("ניהול הכנסות והוצאות 💰")

st.markdown("### תמונת מצב")
col1, col2, col3 = st.columns(3)
col1.metric(label="יתרה נוכחית", value=f"₪ {current_balance:,.2f}")
col2.metric(label="סה\"כ הכנסות", value=f"₪ {total_income:,.2f}")
col3.metric(label="סה\"כ הוצאות", value=f"₪ {total_expenses:,.2f}")

st.divider()

# --- ממשק המשתמש: טופס הוספת פעולה ---
st.markdown("### הוספת פעולה חדשה")
with st.form(key="transaction_form", clear_on_submit=True):
    transaction_type = st.selectbox("סוג הפעולה:", ["הוצאה", "הכנסה"])
    amount = st.number_input("סכום (₪):", min_value=0.0, step=50.0)
    reason = st.text_input("סיבה (חובה להזין):")
    
    submit_button = st.form_submit_button(label="שמור נתונים ועדכן טבלה")
    
    if submit_button:
        if not reason.strip():
            st.error("שגיאה: חובה להזין סיבה כדי לשמור את הפעולה.")
        elif amount <= 0:
            st.error("שגיאה: יש להזין סכום חיובי גדול מאפס.")
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

# --- כלים נוספים: היסטוריה, הורדה וייבוא ---
with st.expander("🛠️ תפריט אפשרויות מתקדם (היסטוריה, ייבוא וייצוא)"):
    
    # 1. תצוגת הטבלה
    st.markdown("**טבלת הנתונים המלאה:**")
    st.dataframe(df, use_container_width=True)
    
    # 2. כפתור הורדה
    st.markdown("**גיבוי נתונים:**")
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "rb") as file:
            st.download_button(
                label="📥 הורד את קובץ האקסל למכשיר שלך",
                data=file,
                file_name=FILE_NAME,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    # 3. ייבוא קובץ ישן / תיקון נתונים
    st.markdown("**העלאת קובץ קודם (ידרוס את הנתונים הקיימים):**")
    uploaded_file = st.file_uploader("בחר קובץ אקסל (.xlsx)", type=['xlsx'])
    
    if uploaded_file is not None:
        if st.button("ייבא והחלף נתונים"):
            try:
                imported_df = pd.read_excel(uploaded_file)
                imported_df.columns = imported_df.columns.str.strip() # הגנה
                imported_df.to_excel(FILE_NAME, index=False)
                st.success("הקובץ הועלה בהצלחה! מרענן...")
                st.rerun()
            except Exception:
                st.error("הייתה שגיאה בקריאת הקובץ. ודא שזהו קובץ אקסל תקני.")
