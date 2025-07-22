import psycopg2

# --- Database Connection Details ---

DB_NAME = "fashion_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

print("Attempting to connect to the database to upgrade...")
try:
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
    cur = conn.cursor()
    
    # === What is being done here? ===
    # We are adding a new column to our existing table to store image vectors.
    # We use 'ADD COLUMN IF NOT EXISTS' to make the script safe to re-run.
    # The vector dimension is 512, which is the standard for the CLIP model we'll use.
    alter_command = "ALTER TABLE products ADD COLUMN IF NOT EXISTS image_embedding vector(512);"
    
    print("Upgrading 'products' table with 'image_embedding' column...")
    cur.execute(alter_command)
    conn.commit()
    print("Table successfully upgraded.")

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if 'cur' in locals(): cur.close()
    if 'conn' in locals(): conn.close()
    print("Database connection closed.")