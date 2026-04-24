import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """Returns a live connection to the CineMatch SQL Server database."""
    server   = os.getenv("SQL_SERVER", r"localhost\SQLEXPRESS")
    database = os.getenv("SQL_DATABASE", "CineMatch")

    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"   # Windows auth — no username/password needed
    )
    return pyodbc.connect(conn_str)
