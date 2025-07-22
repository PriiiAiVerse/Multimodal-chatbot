from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import uuid
from PIL import Image
import numpy as np
from sentence_transformers import SentenceTransformer
from filtered_retrieval import find_filtered_similar_products, find_similar_by_image
from query_analysis import analyze_query_with_llm
import shutil
import psycopg2
from pgvector.psycopg2 import register_vector

# === CONFIG ===
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

DB_NAME = "fashion_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

# === MODEL ===
print("Loading CLIP model for image embeddings...")
clip_model = SentenceTransformer('clip-ViT-B-32')
print("CLIP model loaded.")

# === FASTAPI SETUP ===
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# === ROUTES ===

@app.post("/search")
async def search_products(query: str = Form(...)):
    try:
        analysis = analyze_query_with_llm(query)
        products = find_filtered_similar_products(analysis)
        return {"response_text": "Here are some results:", "products": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/similar-by-image")
async def similar_by_image(product_id: str = Form(...)):
    try:
        products = find_similar_by_image(product_id)
        return {"response_text": "Products visually similar to this:", "products": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-and-search")
async def upload_and_search(file: UploadFile = File(...)):
    try:
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png"]:
            raise HTTPException(status_code=400, detail="Only jpg, jpeg, png files allowed")

        filename = f"{uuid.uuid4().hex}.{ext}"
        image_path = os.path.join(UPLOAD_DIR, filename)

        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        image = Image.open(image_path)
        image_embedding = clip_model.encode(image)

        # Search similar from DB
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        register_vector(conn)
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, summary, price, color, neckline, img_paths 
            FROM products 
            ORDER BY image_embedding <=> %s 
            LIMIT 5
            """,
            (np.array(image_embedding),)
        )
        rows = cur.fetchall()

        results = []
        for row in rows:
            results.append({
                "id": row[0], "summary": row[1], "price": row[2], "color": row[3],
                "neckline": row[4], "image": row[5][0] if row[5] else None
            })

        cur.close()
        conn.close()

        return {"response_text": "Results based on uploaded image:", "products": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
