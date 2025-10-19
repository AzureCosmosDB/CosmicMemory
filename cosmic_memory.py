"""
CosmicMemory - A memory management class for Azure Cosmos DB and OpenAI integration.
"""
import json
import uuid
import tiktoken
from datetime import datetime
from processing import generate_embedding
from cosmos_interface import (
    create_container,
    insert_memory,
    semantic_search,
    recent_memories,
    remove_item,
    get_memories_by_user,
    get_memories_by_thread,
    get_memory_by_id
)

class CosmicMemory:
    """
    A class for managing memories with Azure Cosmos DB and OpenAI embeddings.
    """
    
    def __init__(self):
        """Initialize the CosmicMemory class with default None values."""
        self.subscription_id = None
        self.resource_group_name = None
        self.account_name = None
        self.cosmos_db_endpoint = None
        self.cosmos_db_database = None
        self.cosmos_db_container = None
        self.openai_endpoint = None
        self.openai_embedding_model = None
        self.openai_embedding_dimensions = 512
        self.vector_index = True
    
    def create_memory_store(self):
        """
        Create Cosmos DB database and container with full-text and vector indexing policies.
        """
        try:
            result = create_container(
                self.subscription_id,
                self.resource_group_name,
                self.account_name,
                self.cosmos_db_database,
                self.cosmos_db_container
            )
            return result
        except Exception as e:
            print(f"create_memory_store failed: {e}")
            return False
    
    def add(self, messages, user_id=None):
        """
        Store conversation messages with automatic token counting and optional embeddings.
        """
        try:
            # Generate GUID for user_id if not provided
            if user_id is None:
                user_id = str(uuid.uuid4())
            
            # Add token counts to each message using tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")  # Default encoding for modern models
            messages_with_tokens = []
            for msg in messages:
                msg_copy = msg.copy()
                content = msg_copy.get("content", "")
                token_count = len(encoding.encode(content))
                msg_copy["token_count"] = token_count
                messages_with_tokens.append(msg_copy)
            
            # Create the memory document following the one-turn-per-document model
            memory_document = {
                "id": str(uuid.uuid4()),  # Unique identifier for this memory document
                "user_id": user_id,
                "thread_id": str(uuid.uuid4()),  # Generate a new GUID for thread_id
                "messages": messages_with_tokens,
                "started_at": datetime.now().isoformat() + "Z",
                "ended_at": datetime.now().isoformat() + "Z"
            }
            
            # Generate embedding if vector_index is enabled
            if self.vector_index:
                # Generate embedding using interface function
                embedding = generate_embedding(
                    messages,
                    self.openai_endpoint,
                    self.openai_embedding_model,
                    self.openai_embedding_dimensions
                )
                
                # Add embedding to document if generation was successful
                if embedding is not None:
                    memory_document["embedding"] = embedding
            
            # Convert to JSON string with formatting
            json_output = json.dumps(memory_document, indent=2)
            
            # Insert into Cosmos DB
            result = insert_memory(
                memory_document,
                self.cosmos_db_endpoint,
                self.cosmos_db_database,
                self.cosmos_db_container
            )
            if result:
                print(f"Memory successfully inserted into Cosmos DB")
            else:
                print(f"Failed to insert memory into Cosmos DB")
        except Exception as e:
            print(f"add_mem called but failed")
            print(f"Error: {e}")
            # Still try to print what we have
            try:
                error_document = {
                    "id": user_id,
                    "thread_id": user_id,
                    "messages": messages,
                    "error": str(e)
                }
                print(json.dumps(error_document, indent=2))
            except:
                print(f"Could not serialize data - messages: {messages}, user_id: {user_id}")
    
    def search(self, query, k, return_details=False):
        """
        Search memories using semantic similarity based on query text.
        """
        try:
            # Generate embedding for the query
            query_embedding = generate_embedding(
                [{"content": query}],
                self.openai_endpoint,
                self.openai_embedding_model,
                self.openai_embedding_dimensions
            )
            
            if query_embedding is not None:
                results = semantic_search(
                    query_embedding,
                    k,
                    self.cosmos_db_endpoint,
                    self.cosmos_db_database,
                    self.cosmos_db_container,
                    return_details
                )
                return results
            else:
                print("Failed to generate query embedding for semantic search")
                return None
                
        except Exception as e:
            print(f"search failed: {e}")
            return None
    
    def get_recent(self, k, return_details=False):
        """
        Retrieve the most recent memories ordered by timestamp.
        """
        try:
            # Get most recent memories
            results = recent_memories(
                k,
                self.cosmos_db_endpoint,
                self.cosmos_db_database,
                self.cosmos_db_container,
                return_details
            )
            return results
                
        except Exception as e:
            print(f"get_recent failed: {e}")
            return None
    
    def get_all_by_user(self, user_id, return_details=False):
        """
        Retrieve all memories for a specific user.
        """
        try:
            # Get all memories for this user
            results = get_memories_by_user(
                user_id,
                self.cosmos_db_endpoint,
                self.cosmos_db_database,
                self.cosmos_db_container,
                return_details
            )
            return results
                
        except Exception as e:
            print(f"get_all_by_user failed: {e}")
            return None
    
    def get_all_by_thread(self, thread_id, return_details=False):
        """
        Retrieve all memories for a specific conversation thread.
        """
        try:
            # Get all memories for this thread
            results = get_memories_by_thread(
                thread_id,
                self.cosmos_db_endpoint,
                self.cosmos_db_database,
                self.cosmos_db_container,
                return_details
            )
            return results
                
        except Exception as e:
            print(f"get_all_by_thread failed: {e}")
            return None
    
    def get_id(self, memory_id):
        """
        Retrieve a specific memory by its document ID.
        """
        try:
            # Get the memory by ID
            result = get_memory_by_id(
                memory_id,
                self.cosmos_db_endpoint,
                self.cosmos_db_database,
                self.cosmos_db_container
            )
            return result
                
        except Exception as e:
            print(f"get_id failed: {e}")
            return None
    
    def delete(self, memory_id):
        """
        Remove a memory document from Cosmos DB by its ID.
        """
        try:
            print(f"Arguments - memory_id: {memory_id}")
            
            # Remove the item from Cosmos DB
            result = remove_item(
                memory_id,
                self.cosmos_db_endpoint,
                self.cosmos_db_database,
                self.cosmos_db_container
            )
            
            if result:
                print(f"Memory successfully deleted from Cosmos DB")
            else:
                print(f"Failed to delete memory from Cosmos DB")
        except Exception as e:
            print(f"delete_mem called but failed")
            print(f"Error: {e}")
