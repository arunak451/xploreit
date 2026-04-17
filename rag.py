import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()

XPLOREIT_URL = os.getenv("XPLOREIT_URL", "https://xploreitcorp.com")

chroma_client = chromadb.PersistentClient(path="./chroma_db")
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = chroma_client.get_or_create_collection(
    name="xploreit_knowledge",
    embedding_function=embedding_fn
)


def scrape_website(url: str) -> list:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=10, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        chunks = []
        words = " ".join(lines).split()
        for i in range(0, len(words), 200):
            chunk = " ".join(words[i:i+200])
            chunks.append(chunk)

        return chunks
    except Exception as e:
        print(f"Scrape error {url}: {e}")
        return []


def build_knowledge_base():
    print("Building knowledge base from XploreiT website...")

    urls = [
        "https://xploreitcorp.com",
        "https://xploreitcorp.com/courses",
        "https://xploreitcorp.com/about",
        "https://xploreitcorp.com/contact",
        "https://xploreitcorp.com/admission",
    ]

    all_chunks = []
    for url in urls:
        print(f"Scraping: {url}")
        chunks = scrape_website(url)
        all_chunks.extend(chunks)
        print(f"  -> {len(chunks)} chunks from {url}")

    if not all_chunks:
        print("No content scraped!")
        return

    existing = collection.get()
    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    collection.add(
        documents=all_chunks,
        ids=[f"chunk_{i}" for i in range(len(all_chunks))]
    )
    print(f"Knowledge base ready! {len(all_chunks)} chunks added.")


def retrieve(query: str, n_results: int = 3) -> str:
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    docs = results["documents"][0]
    return "\n\n".join(docs)


if __name__ == "__main__":
    build_knowledge_base()
