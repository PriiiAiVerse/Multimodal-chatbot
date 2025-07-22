import psycopg2

# Database connection settings
DB_NAME = "fashion_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

try:
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()
    print("Connected to the database.")

    # Query the first 10 rows
    cur.execute("SELECT id, category, gender, price, summary FROM products LIMIT 10;")
    rows = cur.fetchall()

    if not rows:
        print("No data found in the 'products' table.")
    else:
        print("\n--- Sample Products ---")
        for row in rows:
            print(f"ID: {row[0]}")
            print(f"Category: {row[1]}")
            print(f"Gender: {row[2]}")
            print(f"Price: {row[3]}")
            print(f"Summary: {row[4]}")
            print("-" * 40)

    cur.close()
    conn.close()
    print("Connection closed.")

except Exception as e:
    print("Error:", e)
