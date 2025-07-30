from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import pickle
import os

def load_faiss_vectorstore():
    index_name = "index"
    base_dir = os.path.dirname(os.path.abspath(__file__))  # path to voice_agent/
    pkl_path = os.path.join(base_dir, f"{index_name}.pkl")

    with open(pkl_path, "rb") as f:
        store = pickle.load(f)
        print("working1")

    vectorstore = FAISS.load_local(
        folder_path=base_dir,
        embeddings=OpenAIEmbeddings(),
        index_name=index_name,
        allow_dangerous_deserialization=True
    )
    print("working2")
    return vectorstore