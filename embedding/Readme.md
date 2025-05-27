"""
## Usage Guide

1. **Setup Environment**
   ```bash
   pip install openai python-docx faiss-cpu numpy tiktoken
   export OPENAI_API_KEY="<your_api_key>"
   ```

2. **Prepare Data Directory**
   - Place all your `.docx` files under the `./data` folder.
   - Ensure the script has read access to this directory.

3. **Run Indexing & Chat**
   ```bash
   python embedding.py
   ```
   - On the first run, the script will index all DOCX files, creating:
     - `faiss.index` (vector index)
     - `chunks.pkl` (serialized text chunks)
     - `meta.json` (file metadata)
   - Subsequent runs will **only** index new or modified files.

4. **Customize Parameters**
   - **DATA_DIR**: Path to your docs folder.
   - **MAX_TOKENS**: Max tokens per text chunk.
   - **TOP_K**: Number of chunks retrieved per query.
   - **EMBEDDING_MODEL** / **CHAT_MODEL**: OpenAI model names.

5. **Example Query**
   - The script runs a sample question (`What does the app architecture look like?`) by default.
   - Modify the `query` variable in `main()` or extend the script to accept CLI args:
     ```python
     import argparse

     parser = argparse.ArgumentParser()
     parser.add_argument("--query", type=str, help="Your question to the indexed docs")
     args = parser.parse_args()
     query = args.query or "What does the app architecture look like?"
     ```

6. **Advanced**
   - Swap FAISS for a remote indexer like Pinecone or Weaviate.
   - Expose as a web service using FastAPI or Flask.
   - Cache embeddings in a database for distributed indexing.
"""