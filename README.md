🧠 Text-to-SQL-to-Execution Converter

A local Streamlit web application that converts natural language questions into SQL queries, executes them on a user-provided SQLite database, and displays the results. Powered by a quantized Defog SQLCoder 7B-2 GGUF model (runs locally via llama.cpp) — no API keys or internet connection required.

Features

User Authentication: Secure login system with admin and guest users.

Local LLM: Uses the Defog SQLCoder 7B-2 GGUF model for converting English questions to SQL.

SQLite Support: Upload your .db files and explore their tables and schema.

SQL Generation: Automatically generates ANSI SQL SELECT queries from plain English questions.

Query Execution: Run generated SQL queries locally and view results in a table format.

Interactive UI: Built with Streamlit for easy, real-time interaction.

Local-only Solution: Works entirely on your machine, no cloud dependency.

Demo

Login with credentials:

Admin:

Username: sake

Password: sake123

Guest:

Username: guest

Password: guest123

Upload your SQLite database (.db file).

Enter a natural language question about your data.

Click “Generate SQL and Run”.

View the generated SQL query and query results instantly.

Installation
Prerequisites

Python 3.10+

CPU with at least 6 threads recommended

SQLite database file for testing

Windows paths are used in code; modify paths for Linux/Mac

Setup

Clone the repository:

git clone <repository-url>
cd <repository-folder>


Create a virtual environment and activate it:

python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate


Install dependencies:

pip install -r requirements.txt


Download the Defog SQLCoder 7B-2 GGUF model and place it locally. Update the path in the code:

model_path = "C:\\Users\\sakec\\Downloads\\sqlcoder-7b-2.Q4_K_M.gguf"


Run the app:

streamlit run app.py

Usage

Login with your username and password.

Upload your SQLite .db file.

Enter a question in plain English (e.g., "Show top 5 orders from Order_details").

Click Generate SQL and Run.

The app generates a SQL query and executes it on your uploaded database.

Results are displayed as a table below the query.

Project Structure
.
├── app.py                  # Main Streamlit app
├── requirements.txt        # Python dependencies
├── sqlcoder-7b-2.Q4_K_M.gguf  # Local LLM model (not included in repo)
└── README.md               # Project documentation

Dependencies

Streamlit
 – Interactive web UI

Pandas
 – Data handling

SQLite3
 – Local database queries

llama_cpp
 – Local LLM integration

streamlit_authenticator
 – Authentication

Notes

Ensure the GGUF model path is correct.

CPU-only mode works but can be slow; GPU support can be enabled by changing n_gpu_layers.

Works locally; no cloud API or token required.

