import os

class Config:
    DB_SERVER = os.getenv("DB_SERVER", "THUHOAI203\SQLEXPRESS")
    DB_DATABASE = os.getenv("DB_DATABASE", "LaptopStore")

    SQL_SERVER_CONN = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_DATABASE};"
        f"Trusted_Connection=yes;"
    )
