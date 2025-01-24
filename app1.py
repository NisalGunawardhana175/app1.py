import streamlit as st
import snowflake.connector

# Snowflake connection
def get_snowflake_connection():
    conn = snowflake.connector.connect(
        user='ALTRIAAPP',
        password='Altria123',
        account='SYB94152',
        warehouse='COMPUTE_WH',
        database='CEAT_DB',
        schema='CEAT_SCHEMA'
    )
    return conn

# Streamlit UI
st.title("Snowflake Streamlit App")
st.write("Connect and Query Snowflake!")

# Query example
if st.button("Fetch Data"):
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM CEAT_TABLE LIMIT 10"
    cursor.execute(query)
    rows = cursor.fetchall()
    st.write(rows)
    cursor.close()
    conn.close()
