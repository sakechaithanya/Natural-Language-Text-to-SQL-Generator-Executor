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
    model_path = "C:\\Users\\sakec\\Downloads\\sqlcoder-7b-2.Q4_K_M.gguf"  # Update path if needed

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
# STEP 2 – Streamlit UI Setup
# --------------------------------------------------
st.title("🧠 Text-to-SQL-to-Execution Converter")
st.info(
    "Upload your SQLite (.db) file, ask in plain English, and get SQL + query results.\n"
    "Running locally with the quantized Defog SQLCoder 7B-2 (GGUF) model — no API key needed."
)

llm = load_model()

# --------------------------------------------------
# STEP 3 – Upload Database
# --------------------------------------------------
uploaded_db = st.file_uploader("📂 Upload SQLite Database (.db)", type=["db"])

if uploaded_db:
    with open("uploaded.db", "wb") as f:
        f.write(uploaded_db.read())
    db_path = "uploaded.db"

    # --------------------------------------------------
    # STEP 4 – Extract and Display Schema
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
    # STEP 5 – SQL Generation Function
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
        text = output["choices"][0]["text"]

        sql_match = re.search(r"SELECT.*?;", text, re.IGNORECASE | re.DOTALL)
        return sql_match.group(0).strip() if sql_match else "ERROR: Could not generate SQL."

    # --------------------------------------------------
    # STEP 6 – SQL Execution Function
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
    # STEP 7 – Normalize SQL (for fair comparison)
    # --------------------------------------------------
    def normalize_sql(sql):
        if not isinstance(sql, str):
            return ""
        sql = sql.strip().lower()
        sql = re.sub(r"\s+", " ", sql)
        sql = re.sub(r";$", "", sql)
        return sql.strip()

    # --------------------------------------------------
    # STEP 8 – User Interaction
    # --------------------------------------------------
    user_query = st.text_input("💬 Enter your question (e.g. ‘Show two records from table Order_details’)")

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

    # --------------------------------------------------
    # STEP 9 – Evaluate Model (Query & Execution Accuracy)
    # --------------------------------------------------
    with st.expander("📊 Evaluate Model Performance"):
        uploaded_eval = st.file_uploader("Upload Evaluation CSV (text, expected_sql)", type=["csv"])

        if uploaded_eval:
            eval_df = pd.read_csv(uploaded_eval)

            if "text" not in eval_df.columns or "expected_sql" not in eval_df.columns:
                st.error("❌ CSV must contain 'text' and 'expected_sql' columns.")
            else:
                st.write("Evaluating model...")

                correct_query = 0
                correct_exec = 0
                total = len(eval_df)

                for _, row in eval_df.iterrows():
                    nl_query = row["text"]
                    expected_sql = normalize_sql(row["expected_sql"])

                    # Generate predicted SQL
                    generated_sql = normalize_sql(generate_sql(nl_query, schema))

                    if expected_sql == generated_sql:
                        correct_query += 1

                    # Execution accuracy test
                    try:
                        gen_res = run_sql(generated_sql + ";", db_path)
                        exp_res = run_sql(expected_sql + ";", db_path)

                        if isinstance(gen_res, pd.DataFrame) and isinstance(exp_res, pd.DataFrame):
                            if gen_res.equals(exp_res):
                                correct_exec += 1
                    except Exception:
                        pass

                query_acc = round((correct_query / total) * 100, 2)
                exec_acc = round((correct_exec / total) * 100, 2)

                st.success(f"✅ Query Accuracy: {query_acc}%")
                st.success(f"⚙️ Execution Accuracy: {exec_acc}%")
