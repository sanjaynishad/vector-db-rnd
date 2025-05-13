import re
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/LaBSE")
client = chromadb.PersistentClient(
    path="./chroma-db", settings=Settings(anonymized_telemetry=False)
)
client.heartbeat()
collection = client.get_or_create_collection(name="hebrew_books")
existing_ids = set(collection.get(include=[], limit=1000000)["ids"])
print(f"Existing IDs: {len(existing_ids)}")


def normalize_hebrew(text: str) -> str:
    text = text.replace("\u200f", "")  # Remove RTL markers
    text = re.sub(r"[^\w\s]", "", text)  # Remove punctuation
    return text.strip()


def embed_text(text: str):
    return model.encode(text).tolist()


def embed_texts(texts: list[str]):
    return model.encode(
        texts, batch_size=32, normalize_embeddings=True, show_progress_bar=True
    ).tolist()


def split_text_into_chunks(text: str, chunk_size: int = 500, overlap: int = 100):
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


def add_document(doc_id: str, text: str, metadata: dict = None):
    if metadata is None:
        metadata = {}

    chunks = split_text_into_chunks(text)

    docs_to_embed = []
    ids_to_use = []
    chunk_metadatas = []

    for idx, raw_text in enumerate(chunks):
        chunk_id = f"{doc_id}_{idx}"
        if chunk_id in existing_ids:  # collection.get(ids=[chunk_id])["metadatas"]:
            print(f"Chunk {chunk_id} already exists in the collection. Skipping.")
            return

        cleaned = normalize_hebrew(raw_text)
        docs_to_embed.append(cleaned)
        ids_to_use.append(chunk_id)
        chunk_metadatas.append(
            {"chunk_index": idx, "doc_id": doc_id, "original": raw_text, **metadata}
        )

    collection.add(
        ids=ids_to_use,
        embeddings=embed_texts(docs_to_embed),
        documents=docs_to_embed,
        metadatas=chunk_metadatas,
    )
