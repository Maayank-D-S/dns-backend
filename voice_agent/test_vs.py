# test_vectorstore.py
from dotenv import load_dotenv
load_dotenv()
from rag_utils import load_faiss_vectorstore

if __name__ == "__main__":
    print("Trying to load vectorstore...")
    vs = load_faiss_vectorstore()
    print("Loaded vectorstore:", vs)
