import psycopg2
from pgvector.psycopg2 import register_vector

# --- Database Connection Details ---
DB_NAME = "fashion_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

print("Attempting to connect to the database...")

try:
    #  Fix: Corrected keyword arguments for connection
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

    # Open a cursor to perform database operations
    cur = conn.cursor()

    # Enable the pgvector extension
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Register vector support
    register_vector(conn)

    print("Dropping existing 'products' table (if exists)...")
    cur.execute("DROP TABLE IF EXISTS products;")
    conn.commit()
    print("Dropped.")

    # Create the 'products' table with vector(384) embedding
    create_table_command = """
    CREATE TABLE IF NOT EXISTS products (
        id VARCHAR(255) PRIMARY KEY,
        category VARCHAR(255),
        gender VARCHAR(50),
        description TEXT,
        summary TEXT,
        neckline VARCHAR(200),
        sleeve VARCHAR(200),
        length VARCHAR(200),
        style VARCHAR(200),
        fabric VARCHAR(200),
        occasion VARCHAR(200),
        season VARCHAR(200),
        special_design TEXT,
        price INT,
        color VARCHAR(200),
        img_paths TEXT[],
        embedding vector(384)
    );
    """

    print("Creating the 'products' table if it doesn't exist...")
    cur.execute(create_table_command)

    # Commit the changes
    conn.commit()
    print(" Table 'products' is ready.")

except Exception as e:
    print(f" An error occurred: {e}")

finally:
    if 'cur' in locals() and cur:
        cur.close()
    if 'conn' in locals() and conn:
        conn.close()
    print(" Database connection closed.")
