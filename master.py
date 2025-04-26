from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv
import os

# 1. Extract text page-by-page ------------------------------------------------
def extract_pdf_pages(path: str):
    reader = PdfReader(path)
    return [
        {"page_number": i + 1, "text": pg.extract_text()}
        for i, pg in enumerate(reader.pages)
        if pg.extract_text()        # skip empty pages
    ]

pdf_pages = extract_pdf_pages("Makeathon TUM presentation.pdf")

# 2. Embed -------------------------------------------------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")
dim   = model.get_sentence_embedding_dimension()       # 384

for page in pdf_pages:
    page["embedding"] = model.encode(page["text"]).tolist()  # ndarray -> list

# 3. Persist in Qdrant --------------------------------------------------------
load_dotenv()
client = QdrantClient(os.getenv("QDRANT_HOST"), api_key=os.getenv("QDRANT_API_KEY"))
COLL   = os.getenv("QDRANT_COLLECTION_NAME", "pdf_collection3")

if not client.collection_exists(COLL):
    client.create_collection(
        collection_name=COLL,
        vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
    )

points = [
    models.PointStruct(
        id=idx,
        vector=page["embedding"],
        payload={"text": page["text"], "page_number": page["page_number"]},
    )
    for idx, page in enumerate(pdf_pages)
]

client.upsert(collection_name=COLL, points=points)
print(f"✅ Upserted {len(points)} pages with {dim}-d embeddings into '{COLL}'.")
# 4. Query -------------------------------------------------------------------
query = "What is the main topic of the presentation?"
query_embedding = model.encode(query).tolist()
results = client.search(
    collection_name=COLL,
    query_vector=query_embedding,
    limit=5,
    with_payload=True,
)
print(f"🔍 Found {len(results)} results for query '{query}':")