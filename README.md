# CosmicMemory 🪐🧠

A lightweight Python framework for storing, managing, and retrieving agent memories using Azure Cosmos DB and Azure OpenAI embeddings.

## Overview

CosmicMemory simplifies memory management for AI agents by providing dual storage options: a client-side memory stack for fast, short-term access, and Azure Cosmos DB for persistent storage with advanced search capabilities. Store and retrieve memories from RAM for quick LLM context passing, or persist to Azure Cosmos DB for durability, scalability, and semantic search. Built on Azure's enterprise-grade infrastructure, it handles the complexity of vector embeddings and database operations so you can focus on building intelligent applications.

## Core Functionalities

- **Client-Side Memory Stack** ⚡ - Fast in-memory storage for short-term context and batch operations
- **Database/Container Creation** 🏗️ - Automatically create Azure Cosmos DB database and container with full-text and vector indexing policies for memory storage and retrieval
- **Memory Storage** 💾 - Persist agent conversations with automatic token counting and metadata
- **Vector Embeddings** 🔢 - Generate embeddings using Azure OpenAI for memories, enabling semantic search.
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

### Configuration

1. **Azure Cosmos DB**: Create a database and container in your Azure Cosmos DB account
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
memory.openai_embedding_model = "embedding-deployment-name"
memory.openai_completions_model = "completions-deployment-name"
memory.openai_embedding_dimensions = 512  # desired dimension for embeddings model
# Enable vector indexing for semantic search
memory.vector_index = True
```

### Create Memory Store

Create the Azure Cosmos DB database and container with full-text search and vector indexing policies:

```python
# Create the database and container, if they do not already exist
memory.create_memory_store()
```

This will create a container with:
- **Vector indexing** on the `/embedding` path using quantizedFlat vector index
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

# Write with auto-generated user_id and thread_id
memory.write(messages)

# Write with a specific user ID
memory.write(messages, user_id="user-123")

# Write with a specific thread ID (to continue an existing conversation)
memory.write(messages, thread_id="thread-guid-456")

# Write with both user_id and thread_id
memory.write(messages, user_id="user-123", thread_id="thread-guid-456")
```

### Client-Side Memory Stack

CosmicMemory provides a client-side memory stack for efficient short-term memory management. The stack keeps memories in RAM for quick access and allows batch writes to Azure Cosmos DB when desired (e.g., at the end of a turn or session)

#### Push to Stack

Add memories to the client-side stack without writing to Azure Cosmos DB:

```python
# Add messages to the stack
messages1 = [
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi there!"}
]
memory.push_stack(messages1)

messages2 = [
    {"role": "user", "content": "How are you?"},
    {"role": "assistant", "content": "I'm doing great!"}
]
memory.push_stack(messages2)

# Stack now contains 2 conversation turns in RAM
```

**Note:** `push_stack()` requires exactly 2 elements (one turn) per call.


#### Get from Stack

Retrieve the last k items from the stack to pass to your LLM:

```python
# Get the last 3 conversation turns from the stack
recent_context = memory.get_stack(3)

# Get all items from the stack
all_context = memory.get_stack()
```

**Sample Output:**

```json
[
  [
    {"role": "user", "content": "What's the capital of France?"},
    {"role": "assistant", "content": "Paris is the capital of France."}
  ],
  [
    {"role": "user", "content": "What's the population?"},
    {"role": "assistant", "content": "Paris has about 2.2 million people."}
  ],
  [
    {"role": "user", "content": "What about the metro area?"},
    {"role": "assistant", "content": "The Paris metropolitan area has over 12 million people."}
  ]
]
```

#### Pop from Stack

Remove and return the most recently added element from the stack:

```python
# Remove the most recent conversation turn
last_item = memory.pop_stack()

# Returns the last item added, or None if stack is empty
```

#### Write Stack to Azure Cosmos DB

Persist the accumulated memories from the stack to Azure Cosmos DB. This will add the latest memories since the last write to the container to prevent redundant or duplicate memories. If this is the first write, all the memories in the stack will be added to the container.

```python
# Write all stack items to Azure Cosmos DB
memory.write_stack(user_id="user-123", thread_id="thread-guid-456")

# All memories are now persisted with the same user_id and thread_id
```

#### Clear Stack

Clear the stack after committing or when starting a new conversation:

```python
# Clear all items from the stack
memory.clear_stack()
```

**Example Workflow:**

```python
# Accumulate conversation turns in RAM
memory.push_stack([
    {"role": "user", "content": "What's the capital of France?"},
    {"role": "assistant", "content": "Paris is the capital of France."}
])

memory.push_stack([
    {"role": "user", "content": "What's the population?"},
    {"role": "assistant", "content": "Paris has about 2.2 million people."}
])

# Get recent context for next LLM call
context = memory.get_stack(2)

# When ready, batch persist to database
memory.write_stack(user_id="user-456", thread_id="thread-789")

# Clear stack for next conversation
memory.clear_stack()
```

### Search and Retrieve Memories

#### Semantic Search

Find contextually relevant memories using vector similarity:

```python
# Search for memories related to "weather"
memory.search("weather forecast", k=5)

# Combine filters - search for a user in a specific thread
memory.search("weather forecast", k=5, user_id="user-123", thread_id="thread-guid")

# Include similarity scores in results
memory.search("weather forecast", k=5, return_score=True)

# Include additional details in results (id, user_id, started_at, ended_at)
memory.search("weather forecast", k=5, return_details=True)

```

**Sample usage:**
```python
memory.search("weather forecast", k=5)
```


**Sample Output:**

```json
  {
    "messages": [
      {
        "role": "user",
        "content": "What's the weather like today in Redmond, WA?",
        "token_count": 7
      },
      {
        "role": "assistant",
        "content": "The weather in Redmond, WA will be partly cloudy with a high of 65F.",
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

# Combine filters - recent memories for a user in a specific thread
memory.get_recent(k=10, user_id="user-123", thread_id="thread-guid")

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
  "type": "memory",
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
  "embedding": [],
  "started_at": "2025-10-18T10:00:00Z",
  "ended_at": "2025-10-18T10:00:45Z"
}
```

## API Reference

### CosmicMemory Class

#### Methods

- **`create_memory_store(cosmos_db_database, cosmos_db_container)`** - Create database and container with full-text and vector indexing
- **`write(messages, user_id=None, thread_id=None)`** - Write memories directly to Azure Cosmos DB with automatic token counting and optional embedding generation. Optionally specify user_id and/or thread_id to organize memories by user and conversation thread.
- **`push_stack(messages)`** - Push a conversation turn (2 messages) onto the client-side memory stack for quick access without database writes
- **`get_stack(k=None)`** - Retrieve the last k conversation turns from the client-side stack. If k is not specified, returns the entire stack.
- **`pop_stack()`** - Remove and return the most recently added element from the memory stack.
- **`write_stack(user_id=None, thread_id=None)`** - Write newly accumulated items from memory stack to Azure Cosmos DB.
- **`clear_stack()`** - Clear the client-side memory stack after committing or when starting a new conversation
- **`search(query, k, user_id=None, thread_id=None, return_details=False, return_score=False)`** - Search for semantically similar memories using vector similarity, optionally filtered by user_id and/or thread_id. Set return_score=True to include similarity scores.
- **`get_recent(k, user_id=None, thread_id=None, return_details=False)`** - Retrieve the k most recent memories ordered by timestamp, optionally filtered by user_id and/or thread_id
- **`get_all_by_user(user_id, return_details=False)`** - Retrieve all memories for a specific user.
- **`get_all_by_thread(thread_id, return_details=False)`** - Retrieve all memories for a specific conversation thread.
- **`get_id(memory_id)`** - Retrieve a specific memory by its document id.
- **`delete(memory_id)`** - Delete a memory by its document id.


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
