import sys
import pymysql

# --- Configure your MySQL connection ---
connection = pymysql.connect(
    read_default_file="~/.my.cnf",
    host="z5tron.mysql.pythonanywhere-services.com",
    user='z5tron',
    database='z5tron$hanzi',
    charset='utf8',
    cursorclass=pymysql.cursors.Cursor
)

try:
    with connection.cursor() as cursor:
        
        # --- Prepare batch data ---
        users_to_add = [
            line.split() for line in open(sys.argv[1], 'r')
        ]

        # --- Batch insert ---
        insert_query = "INSERT INTO word (book, chapter, word) VALUES (%s, %s, %s)"
        cursor.executemany(insert_query, users_to_add)

    # --- Commit the transaction ---
    connection.commit()
    print(f"{cursor.rowcount} rows inserted successfully.")

finally:
    connection.close()
