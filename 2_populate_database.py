import json
import psycopg2
import numpy as np
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

# --- Database Connection Details (same as before) ---

DB_NAME = "fashion_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

# === WHAT IS BEING DONE HERE (THE CHANGE) ===
# Instead of a hardcoded list, we now load the data from the external JSON file.
# This is much more scalable and manageable.
try:
    print("Loading product data from products.json...")
    with open('products.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    print(f"Successfully loaded {len(raw_data)} products from file.")
except FileNotFoundError:
    print("Error: 'products.json' not found. Please make sure the file is in the same directory as the script.")
    exit() # Stop the script if the data file doesn't exist.
except json.JSONDecodeError:
    print("Error: Could not parse 'products.json'. Please check if it is a valid JSON format.")
    exit() # Stop the script if the JSON is malformed.


def get_searchable_text(item):
    """Combines key product attributes into a single string for embedding."""
    return f"A {item['color']} {item['gender']} {item['category']} for {item['occasion']}. Style: {item['style']} with a {item['neckline']} neckline. Details: {item['summary']}"

# Load the sentence transformer model
print("Loading sentence transformer model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded.")

# Generate embeddings
print("Generating embeddings for all products...")
searchable_texts = [get_searchable_text(item) for item in raw_data]
embeddings = model.encode(searchable_texts)
print(f"Generated {len(embeddings)} embeddings.")

# Connect to the database and insert data (this part is unchanged)
try:
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
    cur = conn.cursor()
    register_vector(conn)
    print("\nSuccessfully connected to the database.")

    print("Inserting data into the 'products' table...")
    for item, embedding in zip(raw_data, embeddings):
        
        cur.execute(
            """
            INSERT INTO products (
                id, category, gender, description, summary, neckline, sleeve, length, style, 
                fabric, occasion, season, special_design, price, color, img_paths, embedding
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                category=EXCLUDED.category, summary=EXCLUDED.summary, price=EXCLUDED.price, embedding=EXCLUDED.embedding;
            """,
            (
                item['id'], item['category'], item['gender'], item['description'], item['summary'],
                item['neckline'], item['sleeve'], item['length'], item['style'], item['fabric'],
                item['occasion'], item['season'], item['special_design'], item['price'],
                item['color'].strip(), item['img_paths'], np.array(embedding)
            )
        )
    
    conn.commit()
    print(f"Successfully inserted/updated {len(raw_data)} products.")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    if 'cur' in locals() and cur:
        cur.close()
    if 'conn' in locals() and conn:
        conn.close()
    print("Database connection closed.")