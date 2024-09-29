"""
Q&A Assistant with RAG
---------------------------------

This is a simple example of an AI Assistant implemented using the Cel.ai framework.
It serves as a basic demonstration of how to get started with Cel.ai for creating intelligent assistants.

Framework: Cel.ai
License: MIT License

This script is part of the Cel.ai example series and is intended for educational purposes.

Usage:
------
Configure the required environment variables in a .env file in the root directory of the project.
The required environment variables are:
- WEBHOOK_URL: The webhook URL for the assistant, you can use ngrok to create a public URL for your local server.
- TELEGRAM_TOKEN: The Telegram bot token for the assistant. You can get this from the BotFather on Telegram.

Then run this script to see a basic AI assistant in action.

Note:
-----
Please ensure you have the Cel.ai framework installed in your Python environment prior to running this script.
"""
# LOAD ENV VARIABLES
import os
from loguru import logger as log
# Load .env variables
from dotenv import load_dotenv

load_dotenv()


# REMOVE THIS BLOCK IF YOU ARE USING THIS SCRIPT AS A TEMPLATE
# -------------------------------------------------------------
import sys
from pathlib import Path
# Add parent directory to path
path = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(str(path.parents[1]))
# -------------------------------------------------------------

# Import Cel.ai modules
from cel.connectors.telegram import TelegramConnector
from cel.gateway.message_gateway import MessageGateway, StreamMode
from cel.message_enhancers.smart_message_enhancer_openai import SmartMessageEnhancerOpenAI
from cel.assistants.macaw.macaw_assistant import MacawAssistant
from cel.prompt.prompt_template import PromptTemplate
from cel.rag.providers.markdown_rag import MarkdownRAG
from cel.rag.stores.mongo.mongo_store import AtlasStore
from cel.rag.text2vec.cached_openai import CachedOpenAIEmbedding
from cel.rag.text2vec.cache.redis_cache import RedisCache


# Setup prompt
prompt = "You are a Q&A Assistant. Called Celia.\
You can help a user to send money.\
Keep responses short and to the point.\
Don't use markdown formatting in your responses."
    
prompt_template = PromptTemplate(prompt)

# Create the assistant based on the Macaw Assistant 
# NOTE: Make sure to provide api key in the environment variable `OPENAI_API_KEY`
# add this line to your .env file: OPENAI_API_KEY=your-key
# or uncomment the next line and replace `your-key` with your OpenAI API key
ast = MacawAssistant(prompt=prompt_template)



# Configure the MongoDB Atlas Store for storing the RAG model vectors
# The AtlasStore is a wrapper around the MongoDB Atlas Data API
# It allows you to store and retrieve vectors from a MongoDB Atlas cluster
# NOTE: You can create a search index in the Atlas cluster to enable vector search or use the default index

# Example search index definition
# {
#   "mappings": {
#     "dynamic": false,
#     "fields": {
#       "plot_embedding": [
#         {
#           "dimensions": 1536,
#           "similarity": "cosine",
#           "type": "knnVector"
#         }
#       ]
#     }
#   }
# }
atlas_store = AtlasStore(
    collection_name="qa",
    db_name="sample_md",
    index_name="default",
    mongo_uri=os.getenv("MONGO_URI"),
    num_dimensions=1536
)

# Configure the RAG model using the MarkdownRAG provider
# by default it uses the CachedOpenAIEmbedding for text2vec
# and ChromaStore for storing the vectors
#cache = CachedOllamaEmbedding()
#redisCache
cache = CachedOpenAIEmbedding(cache_backend=RedisCache(), CACHE_EXPIRE=3600)

mdm = MarkdownRAG("demo", file_path="examples/10_mongo_atlas_rag/qa.md",text2vec=cache)
# Load from the markdown file, then slice the content, and store it.
mdm.load()
# Register the RAG model with the assistant
ast.set_rag_retrieval(mdm)


# Create the Message Gateway - This component is the core of the assistant
# It handles the communication between the assistant and the connectors
gateway = MessageGateway(
    webhook_url="https://ea7b-181-225-64-137.ngrok-free.app",
    assistant=ast,
    host="127.0.0.1", port=5004,
    message_enhancer=SmartMessageEnhancerOpenAI()
)

# For this example, we will use the Telegram connector
conn = TelegramConnector(
    token="6977012519:AAGQ70yqPG56fdQQJDrRDiZdYYNsOTyd3iQ", 
    stream_mode=StreamMode.FULL
)
# Register the connector with the gateway
gateway.register_connector(conn)

# Then start the gateway and begin processing messages
gateway.run()

