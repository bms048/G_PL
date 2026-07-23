import streamlit as st
import pandas as pd
import datetime
import os

# --- הגדרות בסיסיות (קובץ עצמאי) ---
FILE_NAME = 'my_budget_data.xlsx'
COLUMNS = ['תאריך', 'הכנסות', 'הוצאות', 'סיבה להוצאה']

st.set_page_config(page_title="ניהול תקציב חכם", page_icon="💰", layout="centered")

def get_data():
    """קורא את הנתונים מהקובץ או יוצר תשתית חדשה אם הוא אינו קיים."""
    if os.path.exists(FILE_NAME):
        return pd.read_excel(FILE_NAME)
    # יצירת טבלה ריקה במידה וזו הפעלה ראשונה
    return pd.DataFrame(columns=COLUMNS)

def save_new_entry(entry_data, df):
    """שומר את הנתונים החדשים לקובץ האקסל."""
    new_df = pd.DataFrame([entry_data])
    updated_df = pd.concat([df, new_df], ignore_index=True)
    updated_df.to_excel(FILE_NAME, index=False)
    return updated_df

# טעינת הנתונים
df = get_data()

# חישוב יתרות
total_income = df['הכנסות'].sum() if not df.empty else 0.0
total_expenses = df['הוצאות'].sum() if not df.empty else 0.0
current_balance = total_income - total_expenses

# --- תצוגת הנתונים למשתמש ---
st.title("ניהול הכנסות והוצאות 💰")

st.markdown("### תמונת מצב")
col1, col2, col3 = st.columns(3)
col1.metric(label="יתרה נוכחית", value=f"₪ {current_balance}")
col2.metric(label="סה\"כ הכנסות", value=f"₪ {total_income}")
col3.metric(label="סה\"כ הוצאות", value=f"₪ {total_expenses}")

st.divider()

# --- טופס הזנת נתונים חדשים ---
st.markdown("### הוספת פעולה חדשה")
with st.form(key="transaction_form", clear_on_submit=True):
    transaction_type = st.selectbox("סוג הפעולה:", ["הכנסה", "הוצאה"])
    amount = st.number_input("סכום (₪):", min_value=0.0, step=50.0)
    reason = st.text_input("סיבה (חובה להזין):")
    
    submit_button = st.form_submit_button(label="שמור נתונים")
    
    if submit_button:
        if not reason.strip():
            st.error("שגיאה: חובה להזין סיבה כדי לשמור את הפעולה.")
        elif amount <= 0:
            st.error("שגיאה: יש להזין סכום חיובי גדול מאפס.")
        else:
            # סידור הנתונים לשמירה
            income_val = amount if transaction_type == "הכנסה" else 0.0
            expense_val = amount if transaction_type == "הוצאה" else 0.0
            
            new_entry = {
                'תאריך': datetime.date.today().strftime("%Y-%m-%d"),
                'הכנסות': income_val,
                'הוצאות': expense_val,
                'סיבה להוצאה': reason
            }
            
            # שמירה ורענון המסך
            save_new_entry(new_entry, df)
            st.success("הפעולה נשמרה בהצלחה!")
            st.rerun()

st.divider()

# הצגת היסטוריית הפעולות (אופציונלי, עוזר למעקב)
with st.expander("לחץ כאן לצפייה בטבלת הנתונים המלאה"):
    st.dataframe(df, use_container_width=True)
    st.divider()
st.markdown("### גיבוי והורדת הנתונים")
if os.path.exists(FILE_NAME):
    with open(FILE_NAME, "rb") as file:
        st.download_button(
            label="📥 הורד את קובץ האקסל למכשיר שלך",
            data=file,
            file_name=FILE_NAME,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.divider()
with st.expander("⚙️ ייבוא נתונים מקובץ קיים (יישור קו)"):
    st.markdown("העלה את קובץ האקסל הקודם שלך (למשל Test1.xlsx) כדי להמשיך לעבוד ממנו.")
    uploaded_file = st.file_uploader("בחר קובץ אקסל", type=['xlsx'])
    
    if uploaded_file is not None:
        if st.button("ייבא והחלף נתונים"):
            try:
                # קריאת הקובץ שהועלה
                imported_df = pd.read_excel(uploaded_file)
                # שמירתו כקובץ העבודה של האפליקציה (דורס את הריק)
                imported_df.to_excel(FILE_NAME, index=False)
                st.success("הנתונים נטענו בהצלחה! מרענן...")
                st.rerun()
            except Exception as e:
                st.error("שגיאה בטעינת הקובץ. ודא שזהו קובץ אקסל תקין.")
        st.divider()
with st.expander("⚠️ אזור מסוכן - איפוס אפליקציה"):
    st.markdown("שים לב: פעולה זו תמחק את כל הנתונים שבאפליקציה ולא ניתן יהיה לשחזר אותם!")
    if st.button("🗑️ מחק את כל הנתונים"):
        # יצירת טבלה ריקה מחדש ודריסת הקובץ הקיים
        pd.DataFrame(columns=COLUMNS).to_excel(FILE_NAME, index=False)
        st.success("כל הנתונים נמחקו בהצלחה! האפליקציה אופסה.")
        st.rerun()

    
