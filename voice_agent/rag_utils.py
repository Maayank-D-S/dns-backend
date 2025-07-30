from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import pickle

def load_faiss_vectorstore():
    index_name = "index"
    with open(f"{index_name}.pkl", "rb") as f:
        store = pickle.load(f)
        print("working1")

    vectorstore = FAISS.load_local(
        folder_path=".",  # ← current directory
        embeddings=OpenAIEmbeddings(),
        index_name=index_name,
        
        allow_dangerous_deserialization=True
    )
    print("working2")
    return vectorstore
