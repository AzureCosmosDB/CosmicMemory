# CosmicMemory 🪐🧠

A lightweight Python framework for storing, managing, and retrieving agent memories using Azure Cosmos DB and Azure OpenAI embeddings.

## Overview

CosmicMemory simplifies memory management for AI agents by providing an intuitive interface to persist conversational context, perform semantic search, and retrieve historical interactions. Built on Azure's enterprise-grade infrastructure, it handles the complexity of vector embeddings and database operations so you can focus on building intelligent applications.

## Core Functionalities

- **Memory Storage** 💾 - Persist agent conversations with automatic token counting and metadata
- **Vector Embeddings** 🔢 - Generate embeddings using Azure OpenAI for semantic search
- **Semantic Search** 🔍 - Find contextually relevant memories using vector similarity
- **Recent Memories** 📅 - Retrieve the most recent interactions chronologically
- **Memory Deletion** 🗑️ - Remove specific memories by ID
- **Entra ID Authentication** 🔐 - Secure access using Azure's identity platform

## Setup

### Prerequisites

- Python 3.8+
- Azure Cosmos DB account with a database and container
- Azure OpenAI resource with an embedding model deployed
- Azure authentication configured (Azure CLI login or managed identity)

### Installation

Install the required packages:

```bash
pip install openai azure-cosmos azure-identity tiktoken
```

### Configuration

1. **Azure Cosmos DB**: Create a database and container in your Cosmos DB account
2. **Azure OpenAI**: Deploy an embedding model (e.g., `text-embedding-3-large`)
3. **Authentication**: Run `az login` to authenticate with Azure

## Usage

### Initialize CosmicMemory

```python
from cosmic_memory import CosmicMemory

# Create instance
memory = CosmicMemory()

# Configure Azure resources
memory.cosmos_db_endpoint = "https://your-account.documents.azure.com:443/"
memory.cosmos_db_database = "your-database"
memory.cosmos_db_container = "your-container"

memory.openai_endpoint = "https://your-openai.openai.azure.com/"
memory.openai_embedding_model = "text-embedding-3-large"
memory.openai_embedding_dimensions = 512

# Enable vector indexing for semantic search
memory.vector_index = True
```

### Add Memories

Store conversation turns with automatic token counting:

```python
messages = [
    {"role": "user", "content": "What's the weather like today?"},
    {"role": "assistant", "content": "I don't have access to real-time weather data."}
]

# Add with a specific user ID
memory.AddMem(messages, user_id="user-123")

# Or let it auto-generate a GUID
memory.AddMem(messages)
```

### Search Memories

#### Semantic Search

Find contextually relevant memories using vector similarity:

```python
# Search for memories related to "weather"
memory.SearchMem("weather forecast", k=5, mode="semantic")
```

**Sample Output:**
```
SearchMem called successfully
Arguments - query: weather forecast, k: 5, mode: semantic, return_id: False

Search results (found 2 items):
[
  {
    "messages": [
      {
        "role": "user",
        "content": "What's the weather like today?",
        "token_count": 7
      },
      {
        "role": "assistant",
        "content": "I don't have access to real-time weather data.",
        "token_count": 10
      }
    ]
  }
]
```

#### Recent Memories

Retrieve the most recent interactions:

```python
# Get the 10 most recent memories
memory.SearchMem("", k=10, mode="recent")
```

**Sample Output:**
```
SearchMem called successfully
Arguments - query: , k: 10, mode: recent, return_id: False

Search results (found 3 items):
[
  {
    "messages": [
      {
        "role": "user",
        "content": "Tell me about Python",
        "token_count": 5
      },
      {
        "role": "assistant",
        "content": "Python is a high-level programming language.",
        "token_count": 9
      }
    ]
  }
]
```

### Delete Memories

Remove specific memories by their document ID:

```python
memory.DeleteMem("document-id-here")
```

## Data Model

CosmicMemory stores memories using a one-turn-per-document model:

```json
{
  "id": "unique-guid",
  "user_id": "user-123",
  "threadId": "conversation-guid",
  "messages": [
    {
      "role": "user",
      "content": "Hello!",
      "token_count": 3
    }
  ],
  "embedding": [0.123, -0.456, ...],
  "startedAt": "2025-10-18T10:00:00Z",
  "endedAt": "2025-10-18T10:00:05Z"
}
```

## Architecture

CosmicMemory consists of two main components:

- **`cosmic_memory.py`** - High-level API for memory operations
- **`cosmos_interface.py`** - Low-level functions for Azure service interactions

This separation allows for easy testing and potential reuse of the interface layer.

## Security

All Azure operations use **DefaultAzureCredential** for authentication, supporting:

- Azure CLI authentication (`az login`)
- Managed Identity (in Azure environments)
- Environment variables
- Visual Studio Code authentication
- And other Azure credential sources

No API keys or connection strings are stored in code.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
