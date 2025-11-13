import streamlit as st
import pandas as pd
import sqlite3
import re
from llama_cpp import Llama
import streamlit_authenticator as stauth
from datetime import datetime

# --------------------------------------------------
# STEP 0 – Authentication Setup
# --------------------------------------------------
names = ["SakeChaitanya", "Guest User"]
usernames = ["sake", "guest"]

# Hash plaintext passwords securely (only once)
hasher = stauth.Hasher()
passwords = [hasher.hash("sake123"), hasher.hash("guest123")]

# Define credentials
credentials = {
    "usernames": {
        usernames[0]: {"name": names[0], "password": passwords[0]},
        usernames[1]: {"name": names[1], "password": passwords[1]},
    }
}

# Initialize authenticator
authenticator = stauth.Authenticate(
    credentials,
    "text2sql_app",        # Cookie name
    "auth_key",            # Signature key
    cookie_expiry_days=1   # Session duration
)

# --------------------------------------------------
# STEP 1 – Display Login Form (new syntax)
# --------------------------------------------------
authenticator.login(location="main")

# After login, access status like this:
authentication_status = st.session_state["authentication_status"]
username = st.session_state.get("username")
name = st.session_state.get("name")

# Handle login states
if authentication_status is False:
    st.error("❌ Incorrect username or password")

elif authentication_status is None:
    st.title("Let's Login to Text-to-SQL App")
    st.warning("⚠️ Please enter your username and password")

# --------------------------------------------------
# STEP 2 – Main App (only after successful login)
# --------------------------------------------------
if authentication_status:
    authenticator.logout("🚪 Logout", "sidebar")
    st.sidebar.success(f"👋 Welcome, {name}")

    # Optional role info
    if username == "sake":
        st.sidebar.info("🧑‍💻 You are logged in as Admin.")
    else:
        st.sidebar.info("👤 You are logged in as Guest.")

    # --------------------------------------------------
    # STEP 3 – Load the Quantized SQLCoder (GGUF) Model
    # --------------------------------------------------
    @st.cache_resource
    def load_model():
        """
        Loads the quantized GGUF version of Defog SQLCoder (defog/sqlcoder-7b-2-GGUF).
        Works locally using llama.cpp (CPU compatible).
        """
        model_path = "C:\\Users\\sakec\\Downloads\\sqlcoder-7b-2.Q4_K_M.gguf"  # update if filename differs
        try:
            llm = Llama(
                model_path=model_path,
                n_ctx=4096,
                n_threads=6,        # adjust based on CPU cores
                n_gpu_layers=0,     # set >0 if GPU available
                verbose=False
            )
            st.success("✅ Model loaded successfully (defog/sqlcoder-7b-2-GGUF)")
            return llm
        except Exception as e:
            st.error(f"❌ Failed to load GGUF model: {e}")
            st.stop()

    # --------------------------------------------------
    # STEP 4 – Streamlit UI
    # --------------------------------------------------
    st.title("🧠 Text-to-SQL-to-Execution Converter")
    st.info(
        "Upload your SQLite (.db) file, ask in plain English, and get SQL + query results.\n"
        "Running locally with the quantized Defog SQLCoder 7B-2 (GGUF) model — no token needed."
    )

    llm = load_model()

    # --------------------------------------------------
    # STEP 5 – Upload Database
    # --------------------------------------------------
    uploaded_db = st.file_uploader("📂 Upload SQLite Database (.db)", type=["db"])

    if uploaded_db:
        with open("uploaded.db", "wb") as f:
            f.write(uploaded_db.read())
        db_path = "uploaded.db"

        # --------------------------------------------------
        # STEP 6 – Extract and Display Schema
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
        # STEP 7 – Generate SQL Query from English
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
            if sql_match:
                return sql_match.group(0).strip()
            else:
                return "ERROR: Could not generate SQL."

        # --------------------------------------------------
        # STEP 8 – Execute SQL Query
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
        # STEP 9 – User Interaction
        # --------------------------------------------------
        user_query = st.text_input(
            "💬 Enter your question (e.g. ‘Show two records from table Order_details’)"
        )

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
