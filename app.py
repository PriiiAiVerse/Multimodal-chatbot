import streamlit as st
import requests
import json

API_URL = "http://127.0.0.1:8000"

# Load product metadata
@st.cache_data
def load_product_details():
    with open("products.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["id"]: item for item in data}

product_details = load_product_details()

# --- Streamlit Page Setup ---
st.set_page_config(page_title=" Fashion Chatbot", layout="centered")
st.title(" Fashion Chatbot Assistant")

# Welcome message once
if "chat" not in st.session_state:
    st.session_state.chat = []
    st.session_state.chat.append({
        "type": "bot",
        "text": " Hi there! I'm your Fashion Assistant. Ask me about any fashion item or upload an image to get started."
    })

# === Chat Input and Image Upload ===
user_query = st.chat_input("Type your fashion query or upload an image below...")
uploaded_img = st.file_uploader("📷 Upload a fashion image", type=["jpg", "jpeg", "png"])

# === Handle Text Input ===
if user_query:
    st.session_state.chat.append({"type": "user", "text": user_query})
    with st.spinner("Thinking..."):
        res = requests.post(f"{API_URL}/search", data={"query": user_query})
        if res.status_code == 200:
            response = res.json()
            st.session_state.chat.append({
                "type": "bot",
                "text": response["response_text"],
                "products": response["products"]
            })
        else:
            st.session_state.chat.append({"type": "bot", "text": " Something went wrong while processing your query."})

# === Handle Image Upload ===
if uploaded_img is not None:
    st.session_state.chat.append({"type": "user", "image": uploaded_img})
    with st.spinner("Analyzing image..."):
        files = {"file": (uploaded_img.name, uploaded_img, uploaded_img.type)}
        res = requests.post(f"{API_URL}/upload-and-search", files=files)
        if res.status_code == 200:
            response = res.json()
            st.session_state.chat.append({
                "type": "bot",
                "text": response["response_text"],
                "products": response["products"]
            })
        else:
            st.session_state.chat.append({"type": "bot", "text": " Image upload failed."})

# === Display Chat Messages ===
for msg in st.session_state.chat:
    with st.chat_message("user" if msg["type"] == "user" else "assistant"):
        if msg.get("text"):
            st.markdown(msg["text"])
        if msg.get("image"):
            st.image(msg["image"], width=250)

        if msg.get("products"):
            for p in msg["products"]:
                pid = p["id"]
                info = product_details.get(pid, {})

                st.image(f"{API_URL}/static{p['image']}", width=250, caption=pid)
                st.markdown(f"**{p['summary']}**")  # Show summary above, not inside expander
                st.markdown(f" ₹{p['price']} &nbsp;&nbsp;  *{p['color']}*")

                with st.expander(" Show Similiar Images "):
                    # Only additional images and color here
                    if "img_paths" in info:
                        st.markdown("** More Images:**")
                        img_cols = st.columns(4)
                        for i, img_path in enumerate(info["img_paths"]):
                            with img_cols[i % 4]:
                                st.image(f"{API_URL}/static{img_path}", use_container_width=True)

                    st.markdown(f"🎨 **Available Colors:** {p.get('color', 'Unknown')}")
