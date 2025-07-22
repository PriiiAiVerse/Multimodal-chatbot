import ollama
import json

def analyze_query_with_llm(user_query: str):
    """
    Uses a local LLM to analyze the user's query, extract filters,
    and create a refined search query.
    """

    system_prompt = """
You are an expert AI assistant for a fashion chatbot. Your job is to extract a structured JSON from a user query.

Return a JSON with:
1. "refined_query": Short, keyword-rich version of the request.
2. "filters": Dictionary with any of the following keys (if mentioned):
   - category
   - gender
   - price_lt
   - price_gt
   - color
   - neckline

🚨 Make sure to detect category (like "dresses", "jeans", "coats", "saree", etc.) from keywords like "dress", "gown", "t-shirt", etc., even if it's plural or indirect.

📌 Normalize categories (e.g., "dresses" → "Dress", "jeans" → "Jeans")

Examples:

User: "show me red dresses under 5000"
Response:
{
  "refined_query": "red dress",
  "filters": {
    "category": "Dresses",
    "color": "Red",
    "price_lt": 5000
  }
}

User: "i want a blue v-neck top"
Response:
{
  "refined_query": "blue v-neck top",
  "filters": {
    "category": "Top",
    "color": "Blue",
    "neckline": "v-neck"
  }
}

Now, analyze the following user query. Respond only with JSON.
"""


    try:
        response = ollama.chat(
            model='phi3',
            messages=[
                {'role': 'system', 'content': system_prompt},  # ✅ FIXED HERE
                {'role': 'user', 'content': user_query}
            ],
            options={'temperature': 0.0},
            format='json'
        )

        content = response['message']['content']
        return json.loads(content)

    except Exception as e:
        print(f"An error occurred while analyzing the query: {e}")
        return {
            "refined_query": user_query,
            "filters": {}
        }

# --- Example Usage ---
if __name__ == "__main__":
    print("--- Analyzing a complex query ---")
    query1 = "can you show me dresses under 5000 in dress color with deep or v neck"
    analysis1 = analyze_query_with_llm(query1)
    print(f"Original Query: '{query1}'")
    print("LLM Analysis:")
    print(json.dumps(analysis1, indent=2))

    print("\n" + "-" * 40 + "\n")

    print("--- Analyzing a simpler query ---")
    query2 = "i want to buy a coat for my farewell under 4000"
    analysis2 = analyze_query_with_llm(query2)
    print(f"Original Query: '{query2}'")
    print("LLM Analysis:")
    print(json.dumps(analysis2, indent=2))
