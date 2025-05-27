#!/usr/bin/env python3

"""
Incremental Retrieval-augmented QA over multiple Word docs using OpenAI embeddings and FAISS.
Updated for OpenAI API v1.0+ and latest best practices.
"""

import os
import json
import pickle
import numpy as np
import faiss
from docx import Document
import tiktoken
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Dict, Any
import time
from pathlib import Path

load_dotenv()

# -------- CONFIGURATION --------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Ensure this env var is set
EMBEDDING_MODEL = "text-embedding-3-large"
CHAT_MODEL = "gpt-4o-mini"  # Updated to latest cost-effective model
DATA_DIR = "./data"  # Folder containing .docx files
INDEX_PATH = "faiss.index"
CHUNKS_PATH = "chunks.pkl"
META_PATH = "meta.json"  # Tracks processed files and their mtimes
MAX_TOKENS = 500  # max tokens per chunk
TOP_K = 5  # number of chunks to retrieve per query
BATCH_SIZE = 100  # Increased batch size for better efficiency

# -------- INITIALIZE OPENAI CLIENT --------
client = OpenAI(api_key=OPENAI_API_KEY)

# -------- UTILITIES --------
encoding = tiktoken.get_encoding("cl100k_base")


def load_docx(path: str) -> str:
    """Load text from a .docx file."""
    try:
        doc = Document(path)
        texts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return "\n".join(texts)
    except Exception as e:
        print(f"[ERROR] Failed to load {path}: {e}")
        return ""


def chunk_text(text: str, max_tokens: int = MAX_TOKENS) -> List[str]:
    """Split text into chunks up to max_tokens using sliding window approach."""
    if not text.strip():
        return []

    # Split by sentences first for better chunk boundaries
    sentences = text.replace('\n', ' ').split('. ')
    chunks = []
    current_chunk = []
    current_tokens = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Add period back if it was removed by split
        if not sentence.endswith('.') and not sentence.endswith('!') and not sentence.endswith('?'):
            sentence += '.'

        sentence_tokens = len(encoding.encode(sentence))

        if current_tokens + sentence_tokens > max_tokens and current_chunk:
            # Save current chunk
            chunks.append(' '.join(current_chunk))
            # Start new chunk with overlap (keep last sentence for context)
            current_chunk = [current_chunk[-1]] if current_chunk else []
            current_tokens = len(encoding.encode(current_chunk[0])) if current_chunk else 0

        current_chunk.append(sentence)
        current_tokens += sentence_tokens

    # Add final chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


# -------- METADATA HANDLING --------
def load_meta() -> Dict[str, Any]:
    """Load metadata about processed files."""
    if os.path.exists(META_PATH):
        try:
            with open(META_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load metadata: {e}")
            return {}
    return {}


def save_meta(meta: Dict[str, Any]) -> None:
    """Save metadata about processed files."""
    try:
        with open(META_PATH, 'w') as f:
            json.dump(meta, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save metadata: {e}")


# -------- EMBEDDINGS & INDEX --------
def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Call OpenAI to get embeddings for a list of texts with retry logic."""
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts,
                encoding_format="float"
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"[RETRY] Embedding attempt {attempt + 1} failed: {e}")
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
            else:
                print(f"[ERROR] All embedding attempts failed: {e}")
                raise


def init_index(emb_dim: int) -> faiss.IndexFlatL2:
    """Initialize a new FAISS index for the given embedding dimension."""
    return faiss.IndexFlatL2(emb_dim)


# -------- BUILD/UPDATE INDEX --------
def build_or_update_index() -> tuple:
    """
    Build a new index or update an existing one by only embedding new/changed files.
    Returns the FAISS index and the list of all chunks.
    """
    chunks = []
    meta = load_meta()

    # Load or init index and chunks
    if os.path.exists(INDEX_PATH) and os.path.exists(CHUNKS_PATH):
        print("[INDEX] Loading existing FAISS index and chunks...")
        try:
            index = faiss.read_index(INDEX_PATH)
            with open(CHUNKS_PATH, 'rb') as f:
                chunks = pickle.load(f)
            print(f"[INDEX] Loaded {index.ntotal} existing embeddings and {len(chunks)} chunks")
        except Exception as e:
            print(f"[ERROR] Failed to load existing index: {e}")
            print("[INDEX] Starting fresh...")
            index = None
            chunks = []
    else:
        print("[INDEX] No existing index, initializing a new one...")
        index = None

    # Ensure data directory exists
    Path(DATA_DIR).mkdir(exist_ok=True)

    # Process each .docx in the data directory
    files_processed = 0
    for root, _, files in os.walk(DATA_DIR):
        for fname in files:
            if not fname.lower().endswith('.docx') or fname.startswith('~$'):
                continue

            path = os.path.join(root, fname)
            try:
                mtime = os.path.getmtime(path)
            except OSError:
                print(f"[ERROR] Cannot access file: {path}")
                continue

            # Skip if unchanged
            if path in meta and abs(meta[path]['mtime'] - mtime) < 1:  # 1 second tolerance
                print(f"[SKIP] {path} unchanged, skipping.")
                continue

            print(f"[INDEX] Processing file: {path}")
            text = load_docx(path)
            if not text:
                print(f"[WARN] No content extracted from {path}")
                continue

            new_chunks = chunk_text(text)
            if not new_chunks:
                print(f"[WARN] No chunks created from {path}")
                continue

            print(f"[INDEX] Created {len(new_chunks)} chunks from {path}")

            # Batch embeddings to avoid rate limits
            embeddings = []
            for i in range(0, len(new_chunks), BATCH_SIZE):
                batch = new_chunks[i:i + BATCH_SIZE]
                print(f"[INDEX] Processing batch {i // BATCH_SIZE + 1}/{(len(new_chunks) - 1) // BATCH_SIZE + 1}")
                batch_embeddings = get_embeddings(batch)
                embeddings.extend(batch_embeddings)

                # Rate limiting - be respectful to OpenAI API
                if i + BATCH_SIZE < len(new_chunks):
                    time.sleep(0.1)

            emb_array = np.array(embeddings, dtype='float32')

            # Initialize index if needed
            if index is None:
                index = init_index(emb_array.shape[1])
                print(f"[INDEX] Initialized new FAISS index with dimension {emb_array.shape[1]}")

            # Add new embeddings to FAISS
            index.add(emb_array)

            # Update chunks list and metadata
            start_idx = len(chunks)
            chunks.extend(new_chunks)
            meta[path] = {
                'mtime': mtime,
                'start_idx': start_idx,
                'num_chunks': len(new_chunks)
            }
            files_processed += 1

    if files_processed > 0:
        # Persist index, chunks, and metadata
        print("[INDEX] Saving updated index and metadata...")
        faiss.write_index(index, INDEX_PATH)
        with open(CHUNKS_PATH, 'wb') as f:
            pickle.dump(chunks, f)
        save_meta(meta)
        print(f"[INDEX] Successfully processed {files_processed} files. Total chunks: {len(chunks)}")
    else:
        print("[INDEX] No files needed processing.")

    if index is None:
        print("[WARN] No index created - no valid documents found")
        return None, []

    return index, chunks


# -------- RETRIEVAL & CHAT --------
def retrieve(query: str, index: faiss.IndexFlatL2, chunks: List[str], k: int = TOP_K) -> List[str]:
    """Retrieve top-k relevant chunks for the query."""
    if index is None or not chunks:
        print("[ERROR] No index or chunks available for retrieval")
        return []

    print(f"[RETRIEVE] Embedding and searching for query: '{query[:50]}...'")
    try:
        q_emb = np.array(get_embeddings([query]), dtype='float32')
        D, I = index.search(q_emb, min(k, index.ntotal))
        print(f"[RETRIEVE] Retrieved {len(I[0])} chunks with distances: {D[0][:3]}...")

        # Filter out invalid indices and return chunks
        valid_chunks = []
        for idx in I[0]:
            if 0 <= idx < len(chunks):
                valid_chunks.append(chunks[idx])

        return valid_chunks
    except Exception as e:
        print(f"[ERROR] Retrieval failed: {e}")
        return []


def chat_with_context(query: str, context_chunks: List[str]) -> str:
    """Call chat completion using the retrieved context."""
    if not context_chunks:
        return "I couldn't find relevant information to answer your question."

    print(f"[CHAT] Building prompt with {len(context_chunks)} retrieved context chunks.")

    system_prompt = """You are an expert assistant. Use the provided context to answer the user's question accurately and comprehensively. 

Guidelines:
- Base your answer primarily on the provided context
- If the context doesn't contain enough information, state that clearly
- Provide specific details when available
- Be concise but thorough
- If you need to make inferences, clearly indicate when you're doing so"""

    context = "\n\n---CONTEXT---\n\n".join(context_chunks)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
    ]

    try:
        tool = {"type": "web_search_preview"}
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=1000,
            tools=[tool]
        )
        print("[CHAT] Received response from chat model.")
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERROR] Chat completion failed: {e}")
        return f"I encountered an error while processing your question: {e}"


# -------- INTERACTIVE MODE --------
def interactive_mode(index: faiss.IndexFlatL2, chunks: List[str]) -> None:
    """Run interactive Q&A mode."""
    if index is None or not chunks:
        print("No index available for querying. Please add some .docx files to the data directory.")
        return

    print("\n=== Interactive RAG Q&A Mode ===")
    print("Ask questions about your documents. Type 'quit' to exit.")
    print(f"Index contains {len(chunks)} chunks from your documents.\n")

    while True:
        try:
            query = input("Your question: ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                break
            if not query:
                continue

            print("\n" + "=" * 50)
            relevant_chunks = retrieve(query, index, chunks)
            answer = chat_with_context(query, relevant_chunks)
            print("Answer:")
            print(answer)
            print("=" * 50 + "\n")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error processing query: {e}")

    print("Goodbye!")


# -------- MAIN SCRIPT --------
def main():
    """Main function - builds index and runs interactive mode."""
    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY environment variable not set!")
        print("Please set your OpenAI API key in a .env file or environment variable.")
        return

    print("=== RAG Document Q&A System ===")
    print("=== Starting index build/update phase ===")

    try:
        index, chunks = build_or_update_index()
        print("=== Index ready for retrieval ===")

        # Run interactive mode instead of single example
        interactive_mode(index, chunks)

    except Exception as e:
        print(f"[ERROR] System failed: {e}")
        return


if __name__ == "__main__":
    main()