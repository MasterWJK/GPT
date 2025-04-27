import os
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient

load_dotenv()

# — clients & globals —
openai_client   = OpenAI()  # reads OPENAI_API_KEY from env
qdrant          = QdrantClient(
    url=os.getenv("QDRANT_HOST"),
    api_key=os.getenv("QDRANT_API_KEY"),
)
EMBEDDING_MODEL = "text-embedding-3-small"
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "pdf_collection")

def semantic_search(query: str, top_k: int = 2, threshold: float = 0.5):
    # 1️⃣ Embed your query with OpenAI
    resp = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[query],
    )
    query_vector = resp.data[0].embedding

    # 2️⃣ Fire the new Query API
    qr = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,   # your dense vector
        limit=top_k,          # how many neighbors to return
        with_payload=True,    # pull back your stored page text & page_number
    )                       

    scored_point = qr.points[0]  # type: ignore[attr-defined] :contentReference[oaicite:0]{index=0}

    if scored_point.score < threshold:
        return {}
    else:
        return {
            "score":        scored_point.score,
            "page_number":  scored_point.payload.get("page_number"),
            "text_snippet": scored_point.payload.get("text", "")[:200].replace("\\n", " ")
        }

# Example usage
if __name__ == "__main__":
    r = semantic_search("What solution?", top_k=2)
    print(f"Page {r}")