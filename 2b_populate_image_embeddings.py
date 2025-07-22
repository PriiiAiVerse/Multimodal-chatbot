import json
import psycopg2
import numpy as np
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from PIL import Image
import os

# --- Database Connection Details ---
DB_NAME = "fashion_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

# === Load the CLIP model ===
print("Loading CLIP model...")
model = SentenceTransformer('clip-ViT-B-32')
print("Model loaded.")

# === Load the product data from products.json ===
print("Loading product data from products.json...")
with open('products.json', 'r', encoding='utf-8') as f:
    products_data = json.load(f)

try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()
    register_vector(conn)
    print("\nSuccessfully connected to the database.")

    print("Generating and updating image embeddings...")
    success_count = 0
    skipped_count = 0

    for item in products_data:
        product_id = item['id']

        # --- Adjust the image path to use 'static/' as base directory ---
        relative_img_path = item['img_paths'][0].lstrip('/')  # removes leading slash
        image_path = os.path.join("static", relative_img_path)

        if not os.path.exists(image_path):
            print(f"[Warning] Image not found for product {product_id}: {image_path}. Skipping.")
            skipped_count += 1
            continue

        # --- Generate image embedding ---
        image = Image.open(image_path)
        image_embedding = model.encode(image)

        # --- Update in database ---
        cur.execute(
            "UPDATE products SET image_embedding = %s WHERE id = %s",
            (np.array(image_embedding), product_id)
        )
        print(f"  ✅ Updated image embedding for product: {product_id}")
        success_count += 1

    conn.commit()
    print(f"\n✅ Finished updating embeddings.")
    print(f"✅ Success: {success_count} | ⚠️ Skipped (not found): {skipped_count}")

except Exception as e:
    print(f"\n❌ An error occurred: {e}")
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
    print("Database connection closed.")
