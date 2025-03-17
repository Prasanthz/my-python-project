import mysql.connector

def connect_to_database():
    connection = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="System",
        database="History",
        auth_plugin='mysql_native_password'
    )
    return connection

def initialize_database(connection):
    cursor = connection.cursor()
    cursor.execute("ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'System'")
    cursor.execute("FLUSH PRIVILEGES")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS command_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        command VARCHAR(255),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    connection.commit()
    return cursor