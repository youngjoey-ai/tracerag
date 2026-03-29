import os

# Default Chunking configurations
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 200))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", 50))

LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen-plus")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-v4")
