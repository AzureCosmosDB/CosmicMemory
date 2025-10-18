"""
Cosmos Interface - Functions for interacting with Azure Cosmos DB and OpenAI.
"""
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.cosmos import CosmosClient


def generate_embedding(messages, openai_endpoint, openai_embedding_model, openai_embedding_dimensions):
    """
    Generate embedding vector for given messages using Azure OpenAI.
    
    Args:
        messages: List of dictionaries containing message data
        openai_endpoint: Azure OpenAI endpoint URL
        openai_embedding_model: OpenAI embedding model name
        openai_embedding_dimensions: Dimensions for the embedding model
    
    Returns:
        List of floats representing the embedding vector, or None if generation fails
    """
    try:
        # Concatenate all message content for embedding
        text_to_embed = " ".join([msg.get("content", "") for msg in messages])
        
        # Get Azure credential token
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default"
        )
        
        # Create Azure OpenAI client with Entra ID authentication
        client = AzureOpenAI(
            azure_endpoint=openai_endpoint,
            api_version="2024-02-01",
            azure_ad_token_provider=token_provider
        )
        
        # Generate embedding
        response = client.embeddings.create(
            input=text_to_embed,
            model=openai_embedding_model,
            dimensions=openai_embedding_dimensions
        )
        
        return response.data[0].embedding
    except Exception as e:
        print(f"Warning: Failed to generate embedding - {e}")
        return None


def insert_memory(memory_document, cosmos_db_endpoint, cosmos_db_database, cosmos_db_container):
    """
    Insert a memory document into Cosmos DB container.
    
    Args:
        memory_document: Dictionary containing the memory document to insert
        cosmos_db_endpoint: Azure Cosmos DB endpoint URL
        cosmos_db_database: Database name in Cosmos DB
        cosmos_db_container: Container name in Cosmos DB
    
    Returns:
        The inserted document if successful, None if insertion fails
    """
    try:
        # Get Azure credential
        credential = DefaultAzureCredential()
        
        # Create Cosmos DB client with Entra ID authentication
        client = CosmosClient(
            url=cosmos_db_endpoint,
            credential=credential
        )
        
        # Get database and container references
        database = client.get_database_client(cosmos_db_database)
        container = database.get_container_client(cosmos_db_container)
        
        # Insert the document
        result = container.create_item(body=memory_document)
        return result
    except Exception as e:
        print(f"Warning: Failed to insert memory into Cosmos DB - {e}")
        return None


def semantic_search(query_embedding, k, cosmos_db_endpoint, cosmos_db_database, cosmos_db_container, return_id=False):
    """
    Perform vector search to find semantically similar memories.
    
    Args:
        query_embedding: List of floats representing the query embedding vector
        k: Number of top results to return
        cosmos_db_endpoint: Azure Cosmos DB endpoint URL
        cosmos_db_database: Database name in Cosmos DB
        cosmos_db_container: Container name in Cosmos DB
        return_id: If True, include document id in results (default: False)
    
    Returns:
        List of message objects from matching documents, or None if search fails
    """
    try:
        # Get Azure credential
        credential = DefaultAzureCredential()
        
        # Create Cosmos DB client with Entra ID authentication
        client = CosmosClient(
            url=cosmos_db_endpoint,
            credential=credential
        )
        
        # Get database and container references
        database = client.get_database_client(cosmos_db_database)
        container = database.get_container_client(cosmos_db_container)
        
        # Build SELECT clause based on return_id parameter
        select_clause = "c.id, c.messages" if return_id else "c.messages"
        
        # Perform vector search query
        query = f"""
            SELECT TOP @k {select_clause}
            FROM c
            ORDER BY VectorDistance(c.embedding, @embedding)
        """
        
        parameters = [
            {"name": "@k", "value": k},
            {"name": "@embedding", "value": query_embedding}
        ]
        
        # Execute query
        results = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        return results
    except Exception as e:
        print(f"Warning: Failed to perform semantic search - {e}")
        return None


def recent_memories(k, cosmos_db_endpoint, cosmos_db_database, cosmos_db_container, return_id=False):
    """
    Get the k most recent memory documents ordered by startedAt timestamp.
    
    Args:
        k: Number of most recent items to return
        cosmos_db_endpoint: Azure Cosmos DB endpoint URL
        cosmos_db_database: Database name in Cosmos DB
        cosmos_db_container: Container name in Cosmos DB
        return_id: If True, include document id in results (default: False)
    
    Returns:
        List of message objects from recent documents, or None if query fails
    """
    try:
        # Get Azure credential
        credential = DefaultAzureCredential()
        
        # Create Cosmos DB client with Entra ID authentication
        client = CosmosClient(
            url=cosmos_db_endpoint,
            credential=credential
        )
        
        # Get database and container references
        database = client.get_database_client(cosmos_db_database)
        container = database.get_container_client(cosmos_db_container)
        
        # Build SELECT clause based on return_id parameter
        select_clause = "c.id, c.messages" if return_id else "c.messages"
        
        # Query for most recent memories
        query = f"""
            SELECT TOP @k {select_clause}
            FROM c
            ORDER BY c.startedAt DESC
        """
        
        parameters = [
            {"name": "@k", "value": k}
        ]
        
        # Execute query
        results = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        return results
    except Exception as e:
        print(f"Warning: Failed to retrieve recent memories - {e}")
        return None


def remove_item(item_id, cosmos_db_endpoint, cosmos_db_database, cosmos_db_container):
    """
    Remove a memory document from Cosmos DB by its ID.
    
    Args:
        item_id: The id of the document to delete
        cosmos_db_endpoint: Azure Cosmos DB endpoint URL
        cosmos_db_database: Database name in Cosmos DB
        cosmos_db_container: Container name in Cosmos DB
    
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        # Get Azure credential
        credential = DefaultAzureCredential()
        
        # Create Cosmos DB client with Entra ID authentication
        client = CosmosClient(
            url=cosmos_db_endpoint,
            credential=credential
        )
        
        # Get database and container references
        database = client.get_database_client(cosmos_db_database)
        container = database.get_container_client(cosmos_db_container)
        
        # Delete the item
        # Note: For partitioned containers, you need the partition key value
        # Using item_id as both the id and partition key
        container.delete_item(item=item_id)
        
        return True
    except Exception as e:
        print(f"Warning: Failed to delete item from Cosmos DB - {e}")
        return False
