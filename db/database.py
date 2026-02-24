import mysql.connector


def get_db_connection():
    db = mysql.connector.connect(
        host= "localhost",
        user="root",
        password="",
        database="chatroom",
        autocommit=False
    )
    print("Database connection established.")
    return db


