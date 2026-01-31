import streamlit as st
import mysql.connector
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- DB CONNECTION LOGIC ---
def get_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
        return None

# --- APP UI ---
st.set_page_config(page_title="Team Skill Matrix", page_icon="🛡️")
st.title("Medical Sector Skill Management")
st.markdown("---")

menu = ["Dashboard", "Update Skills", "Compliance Audit"]
choice = st.sidebar.selectbox("Navigation", menu)

if choice == "Dashboard":
    st.subheader("Team Competency Matrix")
    conn = get_connection()
    if conn:
        query = """
        SELECT u.full_name AS Name, s.skill_name AS Skill, 
               s.category AS Category, us.proficiency_level AS Level, 
               us.updated_at AS 'Last Verified'
        FROM user_skills us
        JOIN users u ON us.user_id = u.user_id
        JOIN skills s ON us.skill_id = s.skill_id
        ORDER BY us.updated_at DESC
        """
        df = pd.read_sql(query, conn)
        st.dataframe(df, use_container_width=True, hide_index=True)
        conn.close()

elif choice == "Update Skills":
    st.subheader("Add or Update Proficiency")
    conn = get_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Fetch data for dropdowns
        cursor.execute("SELECT user_id, full_name FROM users")
        all_users = cursor.fetchall()
        cursor.execute("SELECT skill_id, skill_name FROM skills")
        all_skills = cursor.fetchall()

        with st.form("skill_form"):
            user = st.selectbox("Select User", all_users, format_func=lambda x: x['full_name'])
            skill = st.selectbox("Select Skill", all_skills, format_func=lambda x: x['skill_name'])
            level = st.slider("Proficiency (1-5)", 1, 5, 3)
            submit = st.form_submit_button("Submit Update")

            if submit:
                # Loophole prevention: SQL Parameterized Query
                upsert_query = """
                INSERT INTO user_skills (user_id, skill_id, proficiency_level)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE proficiency_level = %s
                """
                cursor.execute(upsert_query, (user['user_id'], skill['skill_id'], level, level))
                conn.commit()
                st.success(f"Verified: {user['full_name']} updated to Level {level} in {skill['skill_name']}")
        
        conn.close()

elif choice == "Compliance Audit":
    st.subheader("Data Integrity Log")
    st.info("In a medical context, every change must be timestamped and traceable.")
    conn = get_connection()
    if conn:
        query = "SELECT * FROM user_skills ORDER BY updated_at DESC"
        df = pd.read_sql(query, conn)
        st.write("Full System Audit Trail:")
        st.table(df) # Static table for audit proof
        conn.close()