# CosmicMemory 🪐🧠

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Azure Cosmos DB](https://img.shields.io/badge/Azure-Cosmos%20DB-0078D4?logo=microsoft-azure)](https://azure.microsoft.com/en-us/products/cosmos-db/)
[![Follow on X](https://img.shields.io/twitter/follow/AzureCosmosDB?style=social)](https://twitter.com/AzureCosmosDB)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Azure%20Cosmos%20DB-0077B5?logo=linkedin)](https://www.linkedin.com/showcase/azure-cosmos-db/)
[![YouTube](https://img.shields.io/badge/YouTube-Azure%20Cosmos%20DB-FF0000?logo=youtube&logoColor=white)](https://www.youtube.com/@AzureCosmosDB)

A lightweight Python framework for storing, managing, and retrieving agent memories using Azure Cosmos DB and Azure OpenAI.

## Table of Contents
- [Overview](#overview)
- [Core Functionalities](#core-functionalities)
- [Setup](#setup)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Usage](#usage)
  - [Initialize CosmicMemory](#initialize-cosmicmemory)
  - [Create Memory Store](#create-memory-store)
  - [Add Memories](#add-memories)
  - [Client-Side Memory Stack](#client-side-memory-stack)
  - [Search and Retrieve Memories](#search-and-retrieve-memories)
  - [Summarize Conversations](#summarize-conversations)
  - [Delete Memories](#delete-memories)
- [Data Models](#data-models)
- [Usage Guidance](#usage-guidance)
- [API Reference](#api-reference)
- [Architecture](#architecture)
- [Security](#security)
- [Future Improvements](#future-improvements)
- [License](#license)

## Overview

CosmicMemory simplifies memory management for AI agents by providing dual storage options: a client-side memory stack for fast, short-term access, and Azure Cosmos DB for persistent storage with advanced search capabilities. Store and retrieve memories from RAM for quick LLM context passing, or persist to Azure Cosmos DB for durability, scalability, and semantic search. 


## Core Functionalities

### Client-Side Memory
- **Push to Stack** ⚡ - Store memories in client-side RAM for immediate access
- **Get from Stack** 📤 - Retrieve recent conversation context instantly for LLM prompts
- **Pop from Stack** ↩️ - Remove the most recent memory from RAM
- **Clear Stack** 🧹 - Reset client-side memory when starting new conversations

### Azure Cosmos DB Memory Persistence
- **Write to Database** 💾 - Persist individual memories directly to Azure Cosmos DB with automatic token counting and embeddings
- **Batch Write Stack** 📦 - Commit multiple accumulated memories from RAM to an Azure Cosmos DB container 
- **Database/Container Creation** 🏗️ - Automatically create Azure Cosmos DB database and container with full-text and vector indexing policies

### Advanced Search & Retrieval
For memories written to Azure Cosmos DB, take advantage of advanced and semantic memories search capabilities:
- **Semantic Search** 🔍 - Find contextually relevant memories using vector similarity and Azure OpenAI embeddings
- **Recent Memories** 📅 - Retrieve the most recent interactions chronologically from persistent storage
- **Filter by User/Thread** 🎯 - Query memories by specific user IDs or conversation threads
- **Similarity Scoring** 📊 - Get relevance scores with semantic search results
- **Thread Summarization** 📝 - Generate LLM-based summaries of conversation threads with key facts extraction
- **Summary Retrieval** 📋 - Retrieve previously generated summaries from persistent storage (Azure Cosmos DB)
- **Memory Deletion** 🗑️ - Remove specific memories by ID from persistent storage

### Security & Infrastructure
- **Entra ID Authentication** 🔐 - Secure access using Azure's identity platform
- **Vector Embeddings** 🔢 - Automatic embedding generation using Azure OpenAI for semantic search capabilities

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
memory.openai_completions_model = "completions-deployment-name"
memory.openai_embedding_model = "embedding-deployment-name"
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
    {"role": "user", "content": "What's the best type of coffee?"},
    {"role": "assistant", "content": "The best type of coffee is the one that makes you happy with every sip."}
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

### Summarize Conversations

#### Generate Summary

Create an AI-powered summary of a conversation thread with key facts extraction:

```python
# Get all memories for a thread
thread_memories = memory.get_all_by_thread("thread-guid-here")

# Generate summary without persisting to database (preview mode)
summary = memory.summarize(
    thread_memories,
    thread_id="thread-guid-here",
    user_id="user-123",
    write=False
)

# Generate and persist summary to Azure Cosmos DB
summary = memory.summarize(
    thread_memories,
    thread_id="thread-guid-here",
    user_id="user-123",
    write=True
)
```

**Sample Output:**

```json
{
  "thread_id": "thread-guid-here",
  "user_id": "user-123",
  "type": "summary",
  "summary": "The user asked about making espresso at home. The assistant provided detailed information about grind settings, dose amounts for different roasts, and extraction timing.",
  "facts": [
    "User is interested in home espresso preparation",
    "Double shot requires 16-19g depending on roast level",
    "Extraction should take 25-30 seconds",
    "Darker roasts need less coffee by weight due to lower density"
  ],
  "token_count": 145,
  "last_updated": "2025-10-19T10:30:00Z"
}
```

**Note:** When `write=False`, the summary is generated for preview without creating embeddings or persisting to the database, saving API calls. When `write=True`, embeddings are generated and the summary is stored in Azure Cosmos DB.

#### Retrieve Summary

Get a previously generated summary for a conversation thread:

```python
# Get summary with just summary and facts
summary = memory.get_summary("thread-guid-here")

# Get summary with additional metadata (thread_id, user_id, token_count, last_updated)
summary = memory.get_summary("thread-guid-here", return_details=True)
```

**Sample Output (with return_details=True):**

```json
{
  "summary": "The user asked about making espresso at home. The assistant provided detailed information about grind settings, dose amounts for different roasts, and extraction timing.",
  "facts": [
    "User is interested in home espresso preparation",
    "Double shot requires 16-19g depending on roast level",
    "Extraction should take 25-30 seconds",
    "Darker roasts need less coffee by weight due to lower density"
  ],
  "thread_id": "thread-guid-here",
  "user_id": "user-123",
  "token_count": 145,
  "last_updated": "2025-10-19T10:30:00Z"
}
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

## Data Models

CosmicMemory stores two types of documents in Azure Cosmos DB:

### Memory Document

One-turn-per-document model for conversation memories:

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

### Summary Document

AI-generated summaries of conversation threads:

```json
{
  "id": "unique-guid",
  "type": "summary",
  "user_id": "user-123",
  "thread_id": "conversation-guid",
  "summary": "The user asked about making espresso at home. The assistant provided detailed information about grind settings, dose amounts for different roasts, and extraction timing.",
  "facts": [
    "User is interested in home espresso preparation",
    "Double shot requires 16-19g depending on roast level",
    "Extraction should take 25-30 seconds",
    "Darker roasts need less coffee by weight due to lower density"
  ],
  "embedding": [],
  "token_count": 145,
  "last_updated": "2025-10-19T10:30:00Z"
}
```

## Usage Guidance

### Memory Storage Patterns

CosmicMemory offers flexible memory management strategies to match your application's needs:

**In-Memory Stack for Active Sessions**  
Use the client-side RAM stack (`push_stack`, `get_stack`, `pop_stack`) to track short-term conversational context during active sessions. This approach provides instant access to recent interactions without database overhead, ideal for maintaining context across multiple LLM calls within a single conversation. Batch persist accumulated memories to Azure Cosmos DB using `write_stack()` when the session concludes or at natural conversation boundaries.

**Direct Database Operations**  
For immediate persistence requirements, use `write()` to store memories directly to Azure Cosmos DB as conversations occur. This ensures data durability from the moment of creation and is well-suited for stateless architectures, long-running conversations, or scenarios where every interaction must be preserved immediately.

### Advanced Retrieval

Leverage Azure Cosmos DB's powerful search capabilities for both memories and summaries:

- **Semantic Search** - Find contextually relevant memories using vector embeddings and similarity scoring, even when exact keywords don't match
- **Filtered Queries** - Retrieve memories scoped to specific users or conversation threads
- **Temporal Access** - Get the most recent interactions chronologically for context continuity

### Thread Summarization Workflow

Optimize long-running conversations with AI-generated summaries:

1. **Generate & Persist** - At the end of conversation threads or sessions, use `summarize()` with `write=True` to create and store thread summaries with extracted key facts
2. **Resume Sessions** - When resuming a conversation, retrieve the summary using `get_summary()` to restore context without loading entire conversation histories
3. **Preview Mode** - Use `summarize()` with `write=False` to generate summaries on-demand without database writes, useful for testing or temporary previews

This pattern reduces token consumption in LLM prompts while maintaining conversational continuity across sessions.

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
- **`summarize(thread_memories, thread_id, user_id, write=False)`** - Generate an AI-powered summary of conversation thread with key facts extraction. When write=True, generates embeddings and persists to Azure Cosmos DB. When write=False, returns summary without embeddings or database writes (preview mode).
- **`get_summary(thread_id, return_details=False)`** - Retrieve a previously generated summary for a conversation thread. When return_details=True, includes thread_id, user_id, token_count, and last_updated fields.
- **`delete(memory_id)`** - Delete a memory by its document id.


## Architecture

CosmicMemory follows a modular architecture with clear separation of concerns:

```
CosmicMemory/
├── cosmic_memory.py          # High-level API and memory orchestration
├── utils/
│   ├── __init__.py          # Package exports
│   ├── cosmos_interface.py  # Azure Cosmos DB operations
│   └── processing.py        # Embedding generation and AI processing
├── mem_test.ipynb           # Usage examples and testing
└── README.md
```

- **`cosmic_memory.py`** - High-level API providing intuitive methods for memory operations, client-side stack management, and orchestration of database and AI operations

- **`utils/cosmos_interface.py`** - Low-level Azure Cosmos DB functions for container creation, document CRUD operations, vector search, and query execution

- **`utils/processing.py`** - AI processing utilities including Azure OpenAI embedding generation, thread summarization, and token counting

## Security

All Azure operations use **DefaultAzureCredential** for authentication, supporting Azure EntraID or Managed Identities, and environment variables. No API keys or connection strings are stored in code.

## Future Improvements

- **Full-Text Search with FullTextContains** - Enable keyword-based memory retrieval using Azure Cosmos DB's full-text search capabilities to complement semantic search with text matching.

- **Hybrid Search Retrieval** - Combine vector similarity search with full-text keyword search using Reciprocal Rank Fusion (RRF) to improve retrieval accuracy by leveraging both semantic understanding and term scoring.

- **Fact-Based Retrieval** - Query and retrieve specific facts extracted from conversation summaries, enabling granular access to key information without processing entire conversation histories.

- **Memory Importance Scoring** - Implement automatic importance weighting for memories based on factors like recency, interaction frequency, and user-defined priorities to surface the most relevant context for LLM prompts.

- **Cross-Thread Memory Links** - Enable relationship mapping between related conversations across different threads, allowing agents to discover and reference relevant context from past interactions on similar topics.

- **Temporal Memory Decay** - Add configurable time-based relevance scoring that gradually reduces the weight of older memories, simulating natural human memory patterns for more contextually appropriate recall.

- **Memory Compression** - Automatically consolidate and compress related memories into higher-level abstractions over time, reducing storage costs and token usage while preserving essential information.


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
