# Testing imports and compatability
import hyperon
import sentence_transformers
from langchain_experimental.text_splitter import SemanticChunker  # type: ignore
from langchain_huggingface import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            