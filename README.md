# CosmicMemory 🪐🧠

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Azure Cosmos DB](https://img.shields.io/badge/Azure-Cosmos%20DB-0078D4?logo=microsoft-azure)](https://azure.microsoft.com/en-us/products/cosmos-db/)
[![Follow on X](https://img.shields.io/twitter/follow/AzureCosmosDB?style=social)](https://twitter.com/AzureCosmosDB)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Azure%20Cosmos%20DB-0077B5?logo=linkedin)](https://www.linkedin.com/showcase/azure-cosmos-db/)
[![YouTube](https://img.shields.io/badge/YouTube-Azure%20Cosmos%20DB-FF0000?logo=youtube&logoColor=white)](https://www.youtube.com/@AzureCosmosDB)

A Python framework for storing, managing, and retrieving agent memories using Azure Cosmos DB and Azure OpenAI, that orchestrates memory processesing on the client. 

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
  - [Client-Side Local Memory](#client-side-local-memory)
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

CosmicMemory simplifies memory management for AI agents by providing dual storage options: a client-side memory (local) for fast, short-term access, and Azure Cosmos DB for persistent storage with advanced search capabilities. Store and retrieve memories from RAM for quick LLM context passing, or persist to Azure Cosmos DB for durability, scalability, and semantic search.

**Two Ways to Store Memories:**

1. **Client-side in-memory** - Store conversation turns in a client-side memory (local) for immediate access during active sessions. Later, write the accumulated memories to Azure Cosmos DB for persistence and enable advanced retrieval inside threads or across-thread semantic search.

2. **Azure Cosmos DB for persistance and advanced retrieval** - Write and read memories directly to and from Azure Cosmos DB for immediate persistence. This approach ensures every interaction is durably stored and immediately available for advanced search and retrieval operations. 

![CosmicMemory Architecture](design.png)

## Core Functionalities

### Client-Side Memory
- **Add to local** ⚡ - Store memories in client-side RAM for immediate access
- **Get from local** 📤 - Retrieve recent conversation context instantly for LLM prompts
- **Pop from local** ↩️ - Remove the most recent memory from RAM
- **Clear local** 🧹 - Reset client-side memory when starting new conversations

### Azure Cosmos DB Memory Persistence
- **Write to Database** 💾 - Persist individual memories directly to Azure Cosmos DB with automatic token counting and embeddings
- **Write Local to Daatabase** 📦 - Commit multiple accumulated memories from RAM to an Azure Cosmos DB container 
- **Database/Container Creation** 🏗️ - Automatically create Azure Cosmos DB database and container with full-text and vector indexing policies

### Advanced Search & Retrieval in Azure Cosmos DB
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
2. **Azure OpenAI**: Deploy an embedding model (e.g., `text-embedding-3-large`) and completions model (e.g., `gpt-5-mini`)
3. **Authentication**: Run `az login` to authenticate with Azure

## Usage

### Initialize CosmicMemory

```python
from cosmic_memory import CosmicMemory

# Create instance
memory = CosmicMemory()

# Option 1: Load configuration from .env file or environment variables
memory.load_config()  # Loads from .env in current directory, and automatically connects to Cosmos DB and Azure OpenAI
# or
memory.load_config('.env')  # Loads from specific file, and automatically connects to Cosmos DB and Azure OpenAI

# Option 2: Configure Azure resources manually
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

# When configuring manually, you must explicitly connect to both services
memory.connect_to_cosmosdb()
memory.connect_to_openai()
```

**Note on Connection Management:**  
CosmicMemory uses single reusable client connections for both Cosmos DB and Azure OpenAI that are initialized when you call `load_config()` or the individual `connect_to_*()` methods. These connections are reused across all operations, eliminating redundant authentication overhead and dramatically improving performance.

**Environment Variables for `load_config()`:**

Create a `.env` file in your project root with your Azure configuration details. You can use the `example.env` file as a template:

```bash
cp example.env .env
# Then edit .env with your actual values
```

Example `.env` file content:

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
    {"role": "agent", "content": "The best type of coffee is the one that makes you happy with every sip."}
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

### Client-Side Local Memory 

CosmicMemory provides a client-side local memory for efficient short-term memory management. The local memory is organized as a nested dictionary structure that maintains separate conversation histories per user and thread: `{user_id: {thread_id: {"messages": [...], "local_index": 0}}}`. This allows you to manage multiple concurrent conversations in RAM and batch write them to Azure Cosmos DB when desired (e.g., at the end of a turn or session).


#### Push to Local Memory

Add memories to the client-side local memory without writing to Azure Cosmos DB:

```python
# Add messages to the local memory for a specific user and thread
messages1 = [
    {"role": "user", "content": "Hello!"},
    {"role": "agent", "content": "Hi there!"}
]
memory.add_local(messages1, user_id="user-123", thread_id="thread-456")

messages2 = [
    {"role": "user", "content": "How are you?"},
    {"role": "agent", "content": "I'm doing great!"}
]
memory.add_local(messages2, user_id="user-123", thread_id="thread-456")

# Local memory now contains 2 conversation turns in RAM for this user/thread combination
```

**Note:** `add_local()` requires exactly 2 elements (one turn) per call.


#### Get from Local Memory

Retrieve the last k items from the local memory for a specific user and thread to pass to your LLM:

```python
# Get the last 3 conversation turns from the local memory for a specific user/thread
recent_context = memory.get_local(user_id="user-123", thread_id="thread-456", k=3)

# Get all items from the local memory for a specific user/thread
all_context = memory.get_local(user_id="user-123", thread_id="thread-456")
```

**Sample Output:**

```json
[
  [
    {"role": "user", "content": "What's the capital of France?"},
    {"role": "agent", "content": "Paris is the capital of France."}
  ],
  [
    {"role": "user", "content": "What's the population?"},
    {"role": "agent", "content": "Paris has about 2.2 million people."}
  ],
  [
    {"role": "user", "content": "What about the metro area?"},
    {"role": "agent", "content": "The Paris metropolitan area has over 12 million people."}
  ]
]
```

#### Pop from Local Memory

Remove and return the most recently added element from the local memory for a specific user and thread:

```python
# Remove the most recent conversation turn for a specific user/thread
last_item = memory.pop_local(user_id="user-123", thread_id="thread-456")

# Returns the last item added, or None if local memory is empty
```

#### Write Local Memory to Azure Cosmos DB

Persist the accumulated memories from the local memory to Azure Cosmos DB. This will add the latest memories since the last write to the container to prevent redundant or duplicate memories. If this is the first write, all the memories in the local memory will be added to the container.

```python
# Write all local memory items for a specific user/thread to Azure Cosmos DB
memory.write_local(user_id="user-123", thread_id="thread-456")

# All memories are now persisted with the specified user_id and thread_id
```

#### Clear Local Memory

Clear the local memory after committing or when starting a new conversation. You can clear all local memory, all threads for a specific user, or a specific user/thread combination:

```python
# Clear all items from all local memory
memory.clear_local()

# Clear all threads for a specific user
memory.clear_local(user_id="user-123")

# Clear a specific user/thread combination
memory.clear_local(user_id="user-123", thread_id="thread-456")
```

**Example Workflow:**

```python
# Accumulate conversation turns in RAM for a specific user/thread
memory.add_local([
    {"role": "user", "content": "What's the capital of France?"},
    {"role": "agent", "content": "Paris is the capital of France."}
], user_id="user-456", thread_id="thread-789")

memory.add_local([
    {"role": "user", "content": "What's the population?"},
    {"role": "agent", "content": "Paris has about 2.2 million people."}
], user_id="user-456", thread_id="thread-789")

# Get recent context for next LLM call
context = memory.get_local(user_id="user-456", thread_id="thread-789", k=2)

# When ready, batch persist to database
memory.write_local(user_id="user-456", thread_id="thread-789")

# Clear local memory for this user/thread when starting a new conversation
memory.clear_local(user_id="user-456", thread_id="thread-789")
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
        "role": "agent",
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
        "role": "agent",
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

#### Summarize In-Memory Local (`summarize_local`)

Generate a summary of conversation turns stored in the client-side local memory (RAM):

```python
# Get memories from the local memory
local_memories = memory.get_local()

# Generate summary without persisting to database (preview mode)
summary = memory.summarize_local(
    local_memories,
    thread_id="thread-guid-here",
    user_id="user-123",
    write=False
)

# Generate and persist summary to Azure Cosmos DB
summary = memory.summarize_local(
    local_memories,
    thread_id="thread-guid-here",
    user_id="user-123",
    write=True
)
```

**Use Case:** Summarize conversations currently held in RAM before writing to the database, useful for session-based summarization.

#### Summarize Database Thread (`summarize_thread`)

Automatically retrieve and summarize an entire conversation thread stored in Azure Cosmos DB:

```python
# Generate summary without persisting (preview mode)
summary = memory.summarize_thread("thread-guid-here", write=False)

# Generate and persist summary to Azure Cosmos DB
summary = memory.summarize_thread("thread-guid-here", write=True)
```

**Use Case:** Summarize complete conversation threads already persisted to Cosmos DB. Automatically retrieves all thread memories and extracts user_id.

**Sample Output:**

```json
{
  "thread_id": "thread-guid-here",
  "user_id": "user-123",
  "type": "summary",
  "summary": "The user asked about making espresso at home. The agent provided detailed information about grind settings, dose amounts for different roasts, and extraction timing.",
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

**Note:** When `write=False`, the summary is generated for preview without creating embeddings or persisting to the database. When `write=True`, embeddings are generated and the summary is stored in Azure Cosmos DB for later retrieval.

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
  "summary": "The user asked about making espresso at home. The agent provided detailed information about grind settings, dose amounts for different roasts, and extraction timing.",
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
      "role": "agent",
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
  "summary": "The user asked about making espresso at home. The agent provided detailed information about grind settings, dose amounts for different roasts, and extraction timing.",
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

**In-Memory Local for Active Sessions**  
Use the client-side local memory (`add_local`, `get_local`, `pop_local`) to track short-term conversational context during active sessions. This approach provides instant access to recent interactions without database overhead, ideal for maintaining context across multiple LLM calls within a single conversation. Batch persist accumulated memories to Azure Cosmos DB using `write_local()` when the session concludes or at natural conversation boundaries.

**Direct Database Operations**  
For immediate persistence requirements, use `write()` to store memories directly to Azure Cosmos DB as conversations occur. This ensures data durability from the moment of creation and is well-suited for stateless architectures, long-running conversations, or scenarios where every interaction must be preserved immediately.

### Advanced Retrieval

Leverage Azure Cosmos DB's powerful search capabilities for both memories and summaries:

- **Semantic Search** - Find contextually relevant memories using vector embeddings and similarity scoring, even when exact keywords don't match
- **Filtered Queries** - Retrieve memories scoped to specific users or conversation threads
- **Temporal Access** - Get the most recent interactions chronologically for context continuity

### Thread Summarization Workflow

Optimize long-running conversations with AI-generated summaries:

1. **Generate & Persist** - At the end of conversation threads or sessions, generate and store thread summaries with extracted key facts:
   - Use `summarize_local(local_memories, thread_id, user_id, write=True)` to summarize in-memory conversations from the client-side local memory
   - Use `summarize_thread(thread_id, write=True)` to automatically retrieve and summarize entire threads already stored in Cosmos DB
2. **Resume Sessions** - When resuming a conversation, retrieve the summary using `get_summary()` to restore context without loading entire conversation histories
3. **Preview Mode** - Use `write=False` with either method to generate summaries on-demand without database writes, useful for testing or temporary previews

This pattern reduces token consumption in LLM prompts while maintaining conversational continuity across sessions.

## API Reference

### CosmicMemory Class

#### Methods

##### Configuration & Connection

- **`load_config(env_file=None)`** - Load configuration from environment variables or .env file. Automatically reads Azure credentials and settings from environment and establishes connections to both Cosmos DB and Azure OpenAI.
- **`connect_to_cosmosdb()`** - Establish a connection to Azure Cosmos DB using the configured endpoint. This method is automatically called by `load_config()`. Only call this manually if you're configuring resources manually instead of using `load_config()`.
- **`connect_to_openai()`** - Establish a connection to Azure OpenAI using the configured endpoint. This method is automatically called by `load_config()`. Only call this manually if you're configuring resources manually instead of using `load_config()`.

##### Database Setup

- **`create_memory_store(cosmos_db_database, cosmos_db_container)`** - Create database and container with full-text and vector indexing

##### Memory Operations

- **`write(messages, user_id=None, thread_id=None)`** - Write memories directly to Azure Cosmos DB with automatic token counting and optional embedding generation. Optionally specify user_id and/or thread_id to organize memories by user and conversation thread.
- **`add_local(messages, user_id, thread_id)`** - Add a conversation turn (2 messages) to the client-side local memory for a specific user and thread. Requires both user_id and thread_id parameters.
- **`get_local(user_id, thread_id, k=None)`** - Retrieve the last k conversation turns from the client-side local memory for a specific user and thread. If k is not specified, returns the entire local memory for that user/thread.
- **`pop_local(user_id, thread_id)`** - Remove and return the most recently added element from the local memory for a specific user and thread.
- **`write_local(user_id, thread_id)`** - Write newly accumulated items from local memory to Azure Cosmos DB for a specific user and thread.
- **`clear_local(user_id=None, thread_id=None)`** - Clear the client-side local memory. Clear all local memory (no params), all threads for a user (user_id only), or a specific user/thread (both params).
- **`search(query, k, user_id=None, thread_id=None, return_details=False, return_score=False)`** - Search for semantically similar memories using vector similarity, optionally filtered by user_id and/or thread_id. Set return_score=True to include similarity scores.
- **`get_recent(k, user_id=None, thread_id=None, return_details=False)`** - Retrieve the k most recent memories ordered by timestamp, optionally filtered by user_id and/or thread_id
- **`get_all_by_user(user_id, return_details=False)`** - Retrieve all memories for a specific user.
- **`get_all_by_thread(thread_id, return_details=False)`** - Retrieve all memories for a specific conversation thread.
- **`get_id(memory_id)`** - Retrieve a specific memory by its document id.
- **`summarize_local(thread_memories, thread_id, user_id, write=False)`** - Generate an AI-powered summary of conversation turns stored in the client-side local memory (RAM). Accepts list of lists format where each inner list contains 2 message objects. When write=True, generates embeddings and persists to Azure Cosmos DB.
- **`summarize_thread(thread_id, write=False)`** - Automatically retrieve all memories for a thread from Cosmos DB and generate a summary. Automatically extracts user_id from the first memory document. When write=True, persists summary to Cosmos DB.
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

- **`cosmic_memory.py`** - High-level API providing intuitive methods for memory operations, client-side memory management, and orchestration of database and AI operations

- **`utils/cosmos_interface.py`** - Low-level Azure Cosmos DB functions for container creation, document CRUD operations, vector search, and query execution

- **`utils/processing.py`** - AI processing utilities including Azure OpenAI embedding generation, thread summarization, and token counting

## Security

All Azure operations use **DefaultAzureCredential** for authentication, supporting Azure EntraID or Managed Identities, and environment variables. No API keys or connection strings are stored in code.

## Future Improvements

- **Performance Optimizations** - Improve overall speed and responsiveness through optimizations including connection pooling, caching strategies, parallel processing, request batching, and reducing unnecessary API calls. Current operations are too slow and need comprehensive performance improvements.

- **Cloud Compute for Data processing** - Offload orchestration of compute-intensive tasks like summary generation, embedding creation, etc. to serverless compute platforms such as Azure Functions. This would enable background processing, improve responsiveness, reduce client-side resource consumption.

- **Async Operations** - Add asynchronous versions of all I/O-bound operations (database writes, searches, embedding generation) to improve performance and enable concurrent processing of multiple memory operations.

- **Bulk Operations** - Implement bulk calls to Azure OpenAI for batch embedding generation and bulk insert operations to Cosmos DB for improved throughput and reduced latency when processing large volumes of memories or conversation histories.

- **Key-Based Authentication Support** - Add support for connection strings and access keys as an alternative to Entra ID (formerly Azure AD) authentication, providing an easier setup path for PoCs, development environments, and users new to Azure and Cosmos DB.

- **Full-Text Search with FullTextContains** - Enable keyword-based memory retrieval using Azure Cosmos DB's full-text search capabilities to complement semantic search with text matching.

- **Hybrid Search Retrieval** - Combine vector similarity search with full-text keyword search using Reciprocal Rank Fusion (RRF) to improve retrieval accuracy by leveraging both semantic understanding and term scoring.

- **Fact-Based Retrieval** - Query and retrieve specific facts extracted from conversation summaries, enabling granular access to key information without processing entire conversation histories.

- **Fact Search and Indexing** - Implement semantic and keyword search capabilities specifically for facts extracted from summaries, with dedicated indexing to enable fast, targeted retrieval of factual information across all conversations and threads.

- **Memory Importance Scoring** - Implement automatic importance weighting for memories based on factors like recency, interaction frequency, and user-defined priorities to surface the most relevant context for LLM prompts.

- **Cross-Thread Memory Links** - Enable relationship mapping between related conversations across different threads, allowing agents to discover and reference relevant context from past interactions on similar topics.

- **Temporal Memory Decay** - Add configurable time-based relevance scoring that gradually reduces the weight of older memories, simulating natural human memory patterns for more contextually appropriate recall.

- **Memory Compression** - Automatically consolidate and compress related memories into higher-level abstractions over time, reducing storage costs and token usage while preserving essential information.


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
