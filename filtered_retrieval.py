import psycopg2
import numpy as np
import json
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from query_analysis import analyze_query_with_llm  # Make sure this file has `system_prompt` not `system_plugin`

# --- Database Connection Details ---

DB_NAME = "fashion_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"


print("Loading sentence transformer model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded.")

def find_filtered_similar_products(analysis: dict, top_k: int = 5):
    """
    Performs a filtered semantic search in the database.

    Args:
        analysis (dict): Output from the LLM: refined query + filters.
        top_k (int): Number of results to return.

    Returns:
        list: List of product dictionaries.
    """
    refined_query = analysis['refined_query']
    filters = analysis.get('filters', {})

    # Create embedding
    query_embedding = model.encode(refined_query)

    # Build WHERE clause
    where_clauses = []
    params = []

    if 'category' in filters:
        where_clauses.append("category = %s")
        params.append(filters['category'])

    if 'color' in filters:
        if isinstance(filters['color'], list):
            where_clauses.append("color = ANY(%s)")
        else:
            where_clauses.append("color = %s")
        params.append(filters['color'])

    if 'neckline' in filters:
        if isinstance(filters['neckline'], list):
            where_clauses.append("neckline = ANY(%s)")
        else:
            where_clauses.append("neckline = %s")
        params.append(filters['neckline'])

    if 'price_lt' in filters:
        where_clauses.append("price < %s")
        params.append(filters['price_lt'])

    if 'price_gt' in filters:
        where_clauses.append("price > %s")
        params.append(filters['price_gt'])

    # Final SQL assembly
    sql_query = "SELECT id, summary, price, color, img_paths FROM products"
    if where_clauses:
        sql_query += " WHERE " + " AND ".join(where_clauses)
    sql_query += " ORDER BY embedding <=> %s LIMIT %s"

    # Final parameters: filters + embedding + limit
    final_params = params + [np.array(query_embedding), top_k]

    # Execute the query
    results = []
    try:
        conn = psycopg2.connect(
            
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        register_vector(conn)
        cur = conn.cursor()

        cur.execute(sql_query, tuple(final_params))
        rows = cur.fetchall()

        for row in rows:
            results.append({
                "id": row[0],
                "summary": row[1],
                "price": row[2],
                "color": row[3],
                "image": row[4][0] if row[4] else None
            })

    except Exception as e:
        print(f"An error occurred during search: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

    return results

# Add this new function to 'filtered_retrieval.py'

def find_similar_by_image(product_id: str, top_k: int = 5):
    """
    Finds visually similar products based on the image embedding of a given product.
    """
    results = []
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        register_vector(conn)
        cur = conn.cursor()
        
        # Step 1: Get the image embedding of the source product.
        cur.execute("SELECT image_embedding FROM products WHERE id = %s", (product_id,))
        source_embedding = cur.fetchone()
        
        if not source_embedding or source_embedding[0] is None:
            print(f"No image embedding found for product {product_id}")
            return []

        source_vector = np.array(source_embedding[0])
        
        # Step 2: Find other products with the closest image embeddings.
        # We search against the 'image_embedding' column and exclude the source product itself.
        cur.execute(
            """
            SELECT id, summary, price, color, neckline, img_paths 
            FROM products 
            WHERE id != %s
            ORDER BY image_embedding <=> %s 
            LIMIT %s
            """,
            (product_id, source_vector, top_k)
        )
        
        rows = cur.fetchall()
        for row in rows:
            results.append({
                "id": row[0], "summary": row[1], "price": row[2], "color": row[3],
                "neckline": row[4], "image": row[5][0] if row[5] else None
            })

    except Exception as e:
        print(f"An error occurred during visual search: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()
            
    return results




# --- Example Usage ---
if __name__ == "__main__":
    user_query_1 = "show me red dresses under 2000 "
    print(f"\n--- Processing Query: '{user_query_1}' ---")

    analysis_1 = analyze_query_with_llm(user_query_1)
    print("LLM Analysis:\n", json.dumps(analysis_1, indent=2))

    search_results_1 = find_filtered_similar_products(analysis_1)

    print("\nSearch Results:")
    if search_results_1:
        for product in search_results_1:
            print(f"  - {product['summary']} | ₹{product['price']}")
    else:
        print("  No products found.")

    print("\n" + "="*50 + "\n")

    user_query_2 = "i want to buy a coat for my farewell under 4000"
    print(f"\n--- Processing Query: '{user_query_2}' ---")

    analysis_2 = analyze_query_with_llm(user_query_2)
    print("LLM Analysis:\n", json.dumps(analysis_2, indent=2))

    search_results_2 = find_filtered_similar_products(analysis_2)

    print("\nSearch Results:")
    if search_results_2:
        for product in search_results_2:
            print(f"  - {product['summary']} | ₹{product['price']}")
    else:
        print("  No products found.")
