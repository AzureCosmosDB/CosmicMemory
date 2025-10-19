# CosmicMemory 🪐🧠

A lightweight Python framework for storing, managing, and retrieving agent memories using Azure Cosmos DB and Azure OpenAI embeddings.

## Overview

CosmicMemory simplifies memory management for AI agents by providing an intuitive interface to persist conversational context, perform semantic search, and retrieve historical interactions. Built on Azure's enterprise-grade infrastructure, it handles the complexity of vector embeddings and database operations so you can focus on building intelligent applications.

## Core Functionalities

- **Database/Container Creation** 🏗️ - Automatically create Azure Cosmos DB database and container with full-text and vector indexing policies for memory storage and retrieval
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
pip install -r requirements.txt
```

Or install packages individually:

```bash
pip install openai azure-cosmos azure-identity azure-mgmt-cosmosdb tiktoken
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
memory.subscription_id = "your-subscription-id"
memory.resource_group_name = "your-resource-group"
memory.account_name = "your-cosmos-account-name"
memory.cosmos_db_endpoint = "https://your-account.documents.azure.com:443/"
memory.cosmos_db_database = "your-database"
memory.cosmos_db_container = "your-container"

memory.openai_endpoint = "https://your-openai.openai.azure.com/"
memory.openai_embedding_model = "text-embedding-3-large"
memory.openai_embedding_dimensions = 512

# Enable vector indexing for semantic search
memory.vector_index = True
```

### Create Memory Store

Create the Cosmos DB database and container with full-text search and vector indexing policies:

```python
# Create the database and container
# If they already exist, the function will do nothing
memory.create_memory_store("your-database", "your-container")
```

This will create a container with:
- **Vector indexing** on the `/embedding` path using quantizedFlat
- **Full-text search indexes** on `/messages/[0]/content` and `/messages/[1]/content`
- **Partition key** on `/thread_id` for efficient thread-based write and read operations
- **Embedding dimensions** of 512 with cosine distance

### Add Memories

Store conversation turns with automatic token counting:

```python
messages = [
    {"role": "user", "content": "What's the weather like today?"},
    {"role": "assistant", "content": "I don't have access to real-time weather data."}
]

# Add with a specific user ID
memory.add(messages, user_id="user-123")

# Or let it auto-generate a GUID
memory.add(messages)
```

### Search and Retrieve Memories

#### Semantic Search

Find contextually relevant memories using vector similarity:

```python
# Search for memories related to "weather"
memory.search("weather forecast", k=5)

# Include additional details in results (id, user_id, started_at, ended_at)
memory.search("weather forecast", k=5, return_details=True)
```

**Sample Output:**

```json
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
```

#### Get Recent Memories

Retrieve the most recent interactions chronologically:

```python
# Get the 10 most recent memories
memory.get_recent(k=10)

# Include additional details in results (id, user_id, started_at, ended_at)
memory.get_recent(k=10, return_details=True)
```

**Sample Output:**

```json
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
```

#### Get All Memories for a User

Retrieve all memories associated with a specific user ID:

```python
# Get all memories for a user
memory.get_all_by_user("user-123")

# Include additional details in results (id, user_id, started_at, ended_at)
memory.get_all_by_user("user-123", return_details=True)
```

#### Get All Memories for a Thread

Retrieve all memories within a specific conversation thread:

```python
# Get all memories for a thread
memory.get_all_by_thread("thread-guid-here")

# Include additional details in results (id, user_id, started_at, ended_at)
memory.get_all_by_thread("thread-guid-here", return_details=True)
```

#### Get Memory by ID

Retrieve a specific memory using its document ID:

```python
# Get a specific memory by its ID
memory.get_id("document-id-here")
```

### Delete Memories

Remove specific memories by their document ID:

```python
memory.delete("document-id-here")
```

**Note:** To get document IDs and metadata, use `return_details=True` when retrieving memories:
```python
memory.search("query", k=5, return_details=True)
memory.get_recent(k=10, return_details=True)
memory.get_all_by_user("user-123", return_details=True)
memory.get_all_by_thread("thread-guid", return_details=True)
```

## Data Model

CosmicMemory stores memories using a one-turn-per-document model:

```json
{
  "id": "unique-guid",
  "user_id": "user-123",
  "thread_id": "conversation-guid",
  "messages": [
    {
      "role": "user",
      "content": "How much fine ground espresso should I use for a double shot?",
      "token_count": 15
    },
    {
      "role": "assistant",
      "content": "For a double shot (about 60ml output), here are the recommended doses:\n\n- **Light roast**: 18-19 grams\n- **Medium roast**: 17-18 grams\n- **Bold/dark roast**: 16-17 grams\n\nDarker roasts are less dense, so you need slightly less by weight. Start with these ranges and adjust based on your taste and extraction time (aim for 25-30 seconds).",
      "token_count": 89
    }
  ],
  "embedding": [0.123, -0.456, ...],
  "started_at": "2025-10-18T10:00:00Z",
  "ended_at": "2025-10-18T10:00:45Z"
}
```

## API Reference

### CosmicMemory Class

#### Methods

- **`create_memory_store(cosmos_db_database, cosmos_db_container)`** - Create database and container with full-text and vector indexing
- **`add(messages, user_id=None)`** - Add memories with automatic token counting and optional embedding generation
- **`search(query, k, return_details=False)`** - Search for semantically similar memories using vector similarity
- **`get_recent(k, return_details=False)`** - Retrieve the k most recent memories ordered by timestamp
- **`get_all_by_user(user_id, return_details=False)`** - Retrieve all memories for a specific user
- **`get_all_by_thread(thread_id, return_details=False)`** - Retrieve all memories for a specific conversation thread
- **`get_id(memory_id)`** - Retrieve a specific memory by its document ID
- **`delete(memory_id)`** - Delete a memory by its document ID

**Note:** When `return_details=True`, retrieval methods return additional fields: `id`, `user_id`, `started_at`, and `ended_at` along with `messages`.

#### Configuration parameters

- `subscription_id` - Azure subscription ID
- `resource_group_name` - Resource group containing the Cosmos DB account
- `account_name` - Cosmos DB account name
- `cosmos_db_endpoint` - Cosmos DB endpoint URL
- `cosmos_db_database` - Database name
- `cosmos_db_container` - Container name
- `openai_endpoint` - Azure OpenAI endpoint URL
- `openai_embedding_model` - Embedding model name
- `openai_embedding_dimensions` - Embedding dimensions (default: 512)
- `vector_index` - Define if vector index should be used and vectors should be generated for memories (default: True)

## Architecture

CosmicMemory consists of three main components:

- **`cosmic_memory.py`** - High-level API for memory operations
- **`cosmos_interface.py`** - Low-level functions for Azure Cosmos DB interactions
- **`processing.py`** - Data processing functions including embedding generation

This separation allows for easy testing and potential reuse of the interface layer.

## Security

All Azure operations use **DefaultAzureCredential** for authentication, supporting:

- Azure EntraID or Managed Identity
- Environment variables
- Visual Studio Code authentication
- And other Azure credential sources

No API keys or connection strings are stored in code.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
