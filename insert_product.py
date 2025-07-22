import psycopg2
import numpy as np

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="fashion_db",
    user="postgres",
    password="postgres"
)
cur = conn.cursor()

# Generate a random 1536-dimensional vector
embedding = np.random.rand(1536).tolist()  # Replace with your real embedding later

# Insert sample product
cur.execute("""
    INSERT INTO products (name, description, image_url, embedding)
    VALUES (%s, %s, %s, %s)
""", (
    "Black T-Shirt",
    "Classic black cotton t-shirt for men.",
    "https://example.com/black-tshirt.jpg",
    embedding
))

conn.commit()
cur.close()
conn.close()

print("✅ Sample product inserted!")
