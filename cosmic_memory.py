"""
CosmicMemory - A memory management class for Azure Cosmos DB and OpenAI integration.
"""
import json
import uuid
import tiktoken
from datetime import datetime
from cosmos_interface import (
    generate_embedding,
    insert_memory,
    semantic_search,
    recent_memories,
    remove_item
)


class CosmicMemory:
    """
    A class for managing memories with Azure Cosmos DB and OpenAI embeddings.
    """
    
    def __init__(self):
        """Initialize the CosmicMemory class with default None values."""
        self.cosmos_db_endpoint = None
        self.cosmos_db_database = None
        self.cosmos_db_container = None
        self.openai_endpoint = None
        self.openai_embedding_model = None
        self.openai_embedding_dimensions = 512
        self.vector_index = False
    
    def AddMem(self, messages, user_id=None):
        """
        Add memories to the database.
        
        Args:
            messages: List of dictionaries containing memory data
            user_id: User/tenant identifier (optional, generates GUID if not provided)
        
        Returns:
            None
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
                "threadId": str(uuid.uuid4()),  # Generate a new GUID for threadId
                "messages": messages_with_tokens,
                "startedAt": datetime.now().isoformat() + "Z",
                "endedAt": datetime.now().isoformat() + "Z"
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
            
            print(f"AddMem called successfully")
            #print(json_output)
            
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
            print(f"AddMem called but failed")
            print(f"Error: {e}")
            # Still try to print what we have
            try:
                error_document = {
                    "id": user_id,
                    "threadId": user_id,
                    "messages": messages,
                    "error": str(e)
                }
                print(json.dumps(error_document, indent=2))
            except:
                print(f"Could not serialize data - messages: {messages}, user_id: {user_id}")
    
    def SearchMem(self, query, k, mode="auto", return_id=False):
        """
        Search for memories in the database.
        
        Args:
            query: Search query string
            k: Number of items to return (integer)
            mode: Search mode - "recent", "semantic", or "auto" (default: "auto")
            return_id: If True, include document id in results (default: False)
        
        Returns:
            None
        """
        try:
            print(f"SearchMem called successfully")
            print(f"Arguments - query: {query}, k: {k}, mode: {mode}, return_id: {return_id}")
            
            results = None
            
            if mode == "semantic":
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
                        return_id
                    )
                else:
                    print("Failed to generate query embedding for semantic search")
            elif mode == "recent":
                # Get most recent memories
                results = recent_memories(
                    k,
                    self.cosmos_db_endpoint,
                    self.cosmos_db_database,
                    self.cosmos_db_container,
                    return_id
                )
            else:
                # Auto mode - could implement logic to choose automatically
                print(f"Mode '{mode}' not implemented. Use 'semantic' or 'recent'.")
            
            # Print results
            if results is not None:
                print(f"\nSearch results (found {len(results)} items):")
                print(json.dumps(results, indent=2))
            else:
                print("No results found or search failed")
                
        except Exception as e:
            print(f"SearchMem called but failed")
            print(f"Arguments - query: {query}, k: {k}, mode: {mode}, return_id: {return_id}")
            print(f"Error: {e}")
    
    def DeleteMem(self, memory_id):
        """
        Delete a memory by its ID.
        
        Args:
            memory_id: ID of the memory to delete
        
        Returns:
            None
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
            print(f"DeleteMem called but failed")
            print(f"Error: {e}")
