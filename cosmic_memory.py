"""
CosmicMemory - A memory management class for Azure Cosmos DB and OpenAI integration.
"""
import json
import uuid
import tiktoken
from datetime import datetime
from utils.processing import generate_embedding, summarize_thread
from utils.cosmos_interface import (
    create_container,
    insert_memory,
    semantic_search,
    recent_memories,
    remove_item,
    get_memories_by_user,
    get_memories_by_thread,
    get_summary_by_thread,
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
        self.openai_completions_model = None
        self.openai_embedding_model = None
        self.openai_embedding_dimensions = 512
        self.vector_index = True
        self.__memory_stack = []
        self.__stack_index = 0
    
    def create_memory_store(self):
        """
        Create Azure Cosmos DB database and container with full-text and vector indexing policies.
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
    
    def write(self, messages, user_id=None, thread_id=None):
        """
        Store conversation messages with automatic token counting and optional embeddings.
        """
        try:
            # Generate GUID for user_id if not provided
            if user_id is None:
                user_id = str(uuid.uuid4())
            
            # Generate GUID for thread_id if not provided
            if thread_id is None:
                thread_id = str(uuid.uuid4())
            
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
                "type": "memory",
                "user_id": user_id,
                "thread_id": thread_id,  # Use provided thread_id or generated GUID
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
            
            # Insert into Azure Cosmos DB
            result = insert_memory(
                memory_document,
                self.cosmos_db_endpoint,
                self.cosmos_db_database,
                self.cosmos_db_container
            )
            if result:
                print(f"Memory successfully inserted into Azure Cosmos DB")
            else:
                print(f"Failed to insert memory into Azure Cosmos DB")
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

    def push_stack(self, messages):
        """
        Add a list of items to the memory_stack for client-side short-term storage without writing to Azure Cosmos DB.
        """
        if not isinstance(messages, list):
            raise ValueError(f"Input must be a list, got {type(messages).__name__}")
        
        if len(messages) != 2:
            raise ValueError(f"Input list must contain exactly 2 elements, got {len(messages)}")
        
        self.__memory_stack.append(messages)
    
    def write_stack(self, user_id=None, thread_id=None):
        """
        Commit new items from memory_stack to Azure Cosmos DB, starting from stack_index. Only writes items that haven't been persisted yet.
        """
        # Write items starting from stack_index + 1 (items after the last written index)
        
        for i in range(self.__stack_index, len(self.__memory_stack)):
            messages = self.__memory_stack[i]
            self.write(messages, user_id=user_id, thread_id=thread_id)
        
        # Update stack_index to the last index written
        self.__stack_index = max(len(self.__memory_stack) - 1,0)
        
    
    def get_stack(self, k=None):
        """
        Get the last k elements from memory_stack for passing to LLM without reading from Azure Cosmos DB. If k is not specified, returns the entire memory_stack.
        """
        if k is None:
            return self.__memory_stack
        return self.__memory_stack[-k:] if k > 0 else []
    
    def pop_stack(self):
        """
        Remove and return the most recently added element from memory_stack.
        """
        if len(self.__memory_stack) > 0:
            result = self.__memory_stack.pop()
            
            # Update stack_index if necessary
            if len(self.__memory_stack) - 1 < self.__stack_index:
                self.__stack_index = len(self.__memory_stack) - 1
            
            return result
        return None
    
    def clear_stack(self):
        """
        Clear the client-side memory_stack after committing or when starting a new conversation.
        """
        self.__memory_stack = []
        self.__stack_index = 0
    
    def search(self, query, k, user_id=None, thread_id=None, return_details=False, return_score=False):
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
                    user_id,
                    thread_id,
                    return_details,
                    return_score
                )
                return results
            else:
                print("Failed to generate query embedding for semantic search")
                return None
                
        except Exception as e:
            print(f"search failed: {e}")
            return None
    
    def get_recent(self, k, user_id=None, thread_id=None, return_details=False):
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
                user_id,
                thread_id,
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
    
    def summarize(self, thread_memories, thread_id, user_id, write=False):
        """
        Generate a summary of thread memories using Azure OpenAI.

        """
        try:
            summary_document = summarize_thread(
                thread_memories,
                thread_id,
                user_id,
                self.openai_endpoint,
                self.openai_completions_model,
                self.openai_embedding_model,
                self.openai_embedding_dimensions,
                write
            )
            
            # Insert into Cosmos DB if write is True
            if write and summary_document:
                result = insert_memory(
                    summary_document,
                    self.cosmos_db_endpoint,
                    self.cosmos_db_database,
                    self.cosmos_db_container
                )
                if result:
                    print(f"Summary successfully inserted into Cosmos DB")
                else:
                    print(f"Failed to insert summary into Cosmos DB")
            
            return summary_document
        except Exception as e:
            print(f"summarize failed: {e}")
            return None
    
    def get_summary(self, thread_id, return_details=False):
        """
        Retrieve the summary document for a specific thread from Cosmos DB.
        """
        try:
            result = get_summary_by_thread(
                thread_id,
                self.cosmos_db_endpoint,
                self.cosmos_db_database,
                self.cosmos_db_container,
                return_details
            )
            return result
        except Exception as e:
            print(f"get_summary failed: {e}")
            return None
    
    def delete(self, memory_id):
        """
        Remove a memory document from Azure Cosmos DB by its ID.
        """
        try:
            print(f"Arguments - memory_id: {memory_id}")
            
            # Remove the item from Azure Cosmos DB
            result = remove_item(
                memory_id,
                self.cosmos_db_endpoint,
                self.cosmos_db_database,
                self.cosmos_db_container
            )
            
            if result:
                print(f"Memory successfully deleted from Azure Cosmos DB")
            else:
                print(f"Failed to delete memory from Azure Cosmos DB")
        except Exception as e:
            print(f"delete_mem called but failed")
            print(f"Error: {e}")
