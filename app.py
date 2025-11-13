import streamlit as st
import pandas as pd
import sqlite3
import re
from llama_cpp import Llama

# --------------------------------------------------
# STEP 1 – Load the Quantized SQLCoder (GGUF) Model
# --------------------------------------------------
@st.cache_resource
def load_model():
    """
    Loads the quantized GGUF version of Defog SQLCoder (defog/sqlcoder-7b-2-GGUF).
    Works locally using llama.cpp (CPU compatible).
    """
    model_path = "C:\\Users\\sakec\\Downloads\\sqlcoder-7b-2.Q4_K_M.gguf" # change if filename differs

    try:
        llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=6,        # adjust based on CPU cores
            n_gpu_layers=0,     # set >0 if you have GPU
            verbose=False
        )
        st.success("✅ Model loaded successfully (defog/sqlcoder-7b-2-GGUF)")
        return llm
    except Exception as e:
        st.error(f"❌ Failed to load GGUF model: {e}")
        st.stop()

# --------------------------------------------------
# Streamlit UI
# --------------------------------------------------
st.title("🧠 Text-to-SQL-to-Execution Converter")
st.info(
    "Upload your SQLite (.db) file, ask in plain English, and get SQL + query results.\n"
    "Running locally with the quantized Defog SQLCoder 7B-2 (GGUF) model — no token needed."
)

llm = load_model()

# --------------------------------------------------
# STEP 2 – Upload Database
# --------------------------------------------------
uploaded_db = st.file_uploader("📂 Upload SQLite Database (.db)", type=["db"])

if uploaded_db:
    with open("uploaded.db", "wb") as f:
        f.write(uploaded_db.read())
    db_path = "uploaded.db"

    # --------------------------------------------------
    # STEP 3 – Extract and Display Schema
    # --------------------------------------------------
    def get_schema(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]

        schema = ""
        for t in tables:
            cursor.execute(f"PRAGMA table_info({t});")
            columns = [c[1] for c in cursor.fetchall()]
            schema += f"\nTable: {t}\nColumns: {columns}\n"
        conn.close()
        return tables, schema

    tables, schema = get_schema(db_path)

    st.subheader("📋 Tables found in the database:")
    st.write(tables)

    # --------------------------------------------------
    # STEP 4 – Generate SQL Query from English
    # --------------------------------------------------
    def generate_sql(nl_query, schema):
        prompt = f"""
        You are an expert SQL developer.
        Based on the following database schema, generate an ANSI SQL SELECT query
        for the given question. Only return the SQL query ending with a semicolon.

        ### Database Schema:
        {schema}

        ### Question:
        {nl_query}

        ### SQL Query:
        """

        output = llm(prompt, max_tokens=512, temperature=0.2)
        print(output)
        text = output["choices"][0]["text"]

        sql_match = re.search(r"SELECT.*?;", text, re.IGNORECASE | re.DOTALL)
        if sql_match:
            return sql_match.group(0).strip()
        else:
            return "ERROR: Could not generate SQL."

    # --------------------------------------------------
    # STEP 5 – Execute SQL Query
    # --------------------------------------------------
    def run_sql(query, db_path):
        try:
            conn = sqlite3.connect(db_path)
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            return f"❌ Error executing SQL: {e}"

    # --------------------------------------------------
    # STEP 6 – User Interaction
    # --------------------------------------------------
    user_query = st.text_input("💬 Enter your question (e.g. ‘Show two records from  table Order_details’)")

    if st.button("🚀 Generate SQL and Run"):
        if user_query.strip():
            with st.spinner("Generating SQL query..."):
                sql_query = generate_sql(user_query, schema)

            st.subheader("🧾 Generated SQL")
            st.code(sql_query, language="sql")

            if not sql_query.startswith("ERROR"):
                with st.spinner("Running SQL..."):
                    result = run_sql(sql_query, db_path)
                    if isinstance(result, pd.DataFrame):
                        st.success("✅ Query executed successfully!")
                        st.dataframe(result)
                    else:
                        st.error(result)
        else:
            st.warning("Please enter a question first.")
