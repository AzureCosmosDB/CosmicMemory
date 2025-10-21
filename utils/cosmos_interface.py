"""
Cosmos Interface - Functions for interacting with Azure Cosmos DB and OpenAI.
"""
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceExistsError
from azure.mgmt.cosmosdb import CosmosDBManagementClient


def _strip_token_counts(messages):
    """
    Helper function to remove token_count from message objects.
    Returns a new list with token_count removed from each message.
    """
    cleaned_messages = []
    for msg in messages:
        cleaned_msg = {k: v for k, v in msg.items() if k != 'token_count'}
        cleaned_messages.append(cleaned_msg)
    return cleaned_messages


def create_container(subscription_id, resource_group_name, account_name, cosmos_db_database, cosmos_db_container):
    """
    Create Cosmos DB database and container with full-text and vector indexing policies.
    """
    try:
        # Get Azure credential
        credential = DefaultAzureCredential()
        
        # Create Cosmos DB Management client
        mgmt_client = CosmosDBManagementClient(credential, subscription_id)
        
        # Create database if it doesn't exist
        try:
            sql_database_create_update_parameters = {
                "location": None,  # Will inherit from account
                "resource": {
                    "id": cosmos_db_database
                },
                "options": {}
            }
            
            poller = mgmt_client.sql_resources.begin_create_update_sql_database(
                resource_group_name=resource_group_name,
                account_name=account_name,
                database_name=cosmos_db_database,
                create_update_sql_database_parameters=sql_database_create_update_parameters
            )
            poller.result()
            print(f"Database '{cosmos_db_database}' created successfully")
        except Exception as e:
            if "already exists" in str(e).lower() or "conflict" in str(e).lower():
                print(f"Database '{cosmos_db_database}' already exists")
            else:
                # If it's not a "already exists" error, check if database exists
                try:
                    mgmt_client.sql_resources.get_sql_database(
                        resource_group_name=resource_group_name,
                        account_name=account_name,
                        database_name=cosmos_db_database
                    )
                    print(f"Database '{cosmos_db_database}' already exists")
                except:
                    raise e
        
        # Define vector embedding policy
        vector_embedding_policy = {
            "vector_embeddings": [
                {
                    "path": "/embedding",
                    "data_type": "float32",
                    "distance_function": "cosine",
                    "dimensions": 512
                }
            ]
        }
        
        # Define indexing policy with vector and full-text search indexes
        indexing_policy = {
            "indexing_mode": "consistent",
            "automatic": True,
            "included_paths": [
                {
                    "path": "/*"
                }
            ],
            "excluded_paths": [
                {
                    "path": "/\"_etag\"/?"
                }
            ],
            "vector_indexes": [
                {
                    "path": "/embedding",
                    "type": "quantizedFlat"
                }
            ],
            "full_text_indexes": [
                {
                    "path": "/messages/[0]/content"
                },
                {
                    "path": "/messages/[1]/content"
                },
                {
                    "path": "/summary"
                }
            ]
        }
        
        # Define full-text search policy
        full_text_policy = {
            "default_language": "en-US",
            "full_text_paths": [
                {
                    "path": "/messages/[0]/content",
                    "language": "en-US"
                },
                {
                    "path": "/messages/[1]/content",
                    "language": "en-US"
                },
                {
                    "path": "/summary",
                    "language": "en-US"
                }
            ]
        }
        
        # Define partition key
        partition_key = {
            "paths": ["/thread_id"],
            "kind": "Hash"
        }
        
        # Create container if it doesn't exist
        try:
            sql_container_create_update_parameters = {
                "location": None,  # Will inherit from account
                "resource": {
                    "id": cosmos_db_container,
                    "partition_key": partition_key,
                    "indexing_policy": indexing_policy,
                    "vector_embedding_policy": vector_embedding_policy,
                    "full_text_policy": full_text_policy
                },
                "options": {}
            }
            
            poller = mgmt_client.sql_resources.begin_create_update_sql_container(
                resource_group_name=resource_group_name,
                account_name=account_name,
                database_name=cosmos_db_database,
                container_name=cosmos_db_container,
                create_update_sql_container_parameters=sql_container_create_update_parameters
            )
            poller.result()
            print(f"Container '{cosmos_db_container}' created successfully with full-text search and vector indexing policies")
        except Exception as e:
            if "already exists" in str(e).lower() or "conflict" in str(e).lower():
                print(f"Container '{cosmos_db_container}' already exists")
            else:
                # If it's not a "already exists" error, check if container exists
                try:
                    mgmt_client.sql_resources.get_sql_container(
                        resource_group_name=resource_group_name,
                        account_name=account_name,
                        database_name=cosmos_db_database,
                        container_name=cosmos_db_container
                    )
                    print(f"Container '{cosmos_db_container}' already exists")
                except:
                    raise e
        
        return True
    except Exception as e:
        print(f"Error: Failed to create database or container - {e}")
        return False


def insert_memory(client, memory_document, cosmos_db_database, cosmos_db_container):
    """
    Insert a memory document into Cosmos DB container.
    
    Args:
        client: CosmosClient instance to use for the operation
        memory_document: The memory document to insert
        cosmos_db_database: Name of the Cosmos DB database
        cosmos_db_container: Name of the Cosmos DB container
    """
    try:
        # Get database and container references
        database = client.get_database_client(cosmos_db_database)
        container = database.get_container_client(cosmos_db_container)
        
        # Insert the document
        result = container.create_item(body=memory_document)
        return result
    except Exception as e:
        print(f"Warning: Failed to insert memory into Cosmos DB - {e}")
        return None


def semantic_search(client, query_embedding, k, cosmos_db_database, cosmos_db_container, user_id=None, thread_id=None, return_details=False, return_score=False):
    """
    Find semantically similar memories using vector similarity search.
    
    Args:
        client: CosmosClient instance to use for the operation
        query_embedding: The embedding vector to search for
        k: Number of results to return
        cosmos_db_database: Name of the Cosmos DB database
        cosmos_db_container: Name of the Cosmos DB container
        user_id: Optional user ID filter
        thread_id: Optional thread ID filter
        return_details: Whether to return detailed metadata
        return_score: Whether to return similarity scores
    """
    try:
        # Get database and container references
        database = client.get_database_client(cosmos_db_database)
        container = database.get_container_client(cosmos_db_container)
        
        # Build SELECT clause based on return_details and return_score parameters
        if return_details and return_score:
            select_clause = "c.id, c.user_id, c.timestamp, c.messages, VectorDistance(c.embedding, @embedding) AS similarity_score"
        elif return_details:
            select_clause = "c.id, c.user_id, c.timestamp, c.messages"
        elif return_score:
            select_clause = "c.messages, VectorDistance(c.embedding, @embedding) AS similarity_score"
        else:
            select_clause = "c.messages"
        
        # Build WHERE clause based on optional filters
        where_conditions = []
        parameters = [
            {"name": "@k", "value": k},
            {"name": "@embedding", "value": query_embedding}
        ]
        
        if user_id is not None:
            where_conditions.append("c.user_id = @user_id")
            parameters.append({"name": "@user_id", "value": user_id})
        
        if thread_id is not None:
            where_conditions.append("c.thread_id = @thread_id")
            parameters.append({"name": "@thread_id", "value": thread_id})
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Perform vector search query
        query = f"""
            SELECT TOP @k {select_clause}
            FROM c
            {where_clause}
            ORDER BY VectorDistance(c.embedding, @embedding)
        """
        
        # Execute query
        # Use partition key if thread_id is specified for better performance
        enable_cross_partition = thread_id is None
        results = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=enable_cross_partition))
        
        # Strip token_count from messages if return_details is False
        if not return_details:
            for result in results:
                if 'messages' in result:
                    result['messages'] = _strip_token_counts(result['messages'])
        
        return results
    except Exception as e:
        print(f"Warning: Failed to perform semantic search - {e}")
        return None


def recent_memories(client, k, cosmos_db_database, cosmos_db_container, user_id=None, thread_id=None, return_details=False):
    """
    Retrieve the k most recent memory documents ordered by timestamp.
    Returns a list of lists, where each inner list contains two message objects (user and assistant) representing one turn.
    
    Args:
        client: CosmosClient instance to use for the operation
        k: Number of recent memories to retrieve
        cosmos_db_database: Name of the Cosmos DB database
        cosmos_db_container: Name of the Cosmos DB container
        user_id: Optional user ID filter
        thread_id: Optional thread ID filter
        return_details: Whether to return detailed metadata
    """
    try:
        # Get database and container references
        database = client.get_database_client(cosmos_db_database)
        container = database.get_container_client(cosmos_db_container)
        
        # Build WHERE clause based on optional filters
        where_conditions = ["c.type = 'memory'"]
        parameters = [{"name": "@k", "value": k}]
        
        if user_id is not None:
            where_conditions.append("c.user_id = @user_id")
            parameters.append({"name": "@user_id", "value": user_id})
        
        if thread_id is not None:
            where_conditions.append("c.thread_id = @thread_id")
            parameters.append({"name": "@thread_id", "value": thread_id})
        
        where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Build SELECT clause based on return_details parameter
        if return_details:
            query = f"""
                SELECT TOP @k c.messages, c.timestamp
                FROM c
                {where_clause}
                ORDER BY c.timestamp DESC
            """
        else:
            query = f"""
                SELECT TOP @k c.messages
                FROM c
                {where_clause}
                ORDER BY c.timestamp DESC
            """
        
        # Execute query
        # Use partition key if thread_id is specified for better performance
        enable_cross_partition = thread_id is None
        results = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=enable_cross_partition))
        
        # Transform results into list of lists format
        # Each document has a 'messages' array with 2 elements (user and assistant)
        formatted_results = []
        for result in results:
            if 'messages' in result and len(result['messages']) == 2:
                if return_details:
                    # Include messages with token counts, plus timestamp
                    turn_data = result['messages'].copy()
                    turn_data.append({
                        "timestamp": result.get('timestamp')
                    })
                    formatted_results.append(turn_data)
                else:
                    # Strip token_count from messages
                    formatted_results.append(_strip_token_counts(result['messages']))
        
        return formatted_results
    except Exception as e:
        print(f"Warning: Failed to retrieve recent memories - {e}")
        return None


def remove_item(client, item_id, cosmos_db_database, cosmos_db_container):
    """
    Delete a memory document from Cosmos DB by its ID.
    
    Args:
        client: CosmosClient instance to use for the operation
        item_id: ID of the item to delete
        cosmos_db_database: Name of the Cosmos DB database
        cosmos_db_container: Name of the Cosmos DB container
    """
    try:
        # Get database and container references
        database = client.get_database_client(cosmos_db_database)
        container = database.get_container_client(cosmos_db_container)
        
        # First, query to get the item and its thread_id
        query = "SELECT * FROM c WHERE c.id = @item_id"
        parameters = [{"name": "@item_id", "value": item_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True))
        
        if not items:
            print(f"Warning: Item with id {item_id} not found")
            return False
        
        thread_id = items[0].get("thread_id")
        
        # Delete the item using the correct partition key
        container.delete_item(item=item_id, partition_key=thread_id)
        
        return True
    except Exception as e:
        print(f"Warning: Failed to delete item from Cosmos DB - {e}")
        return False


def get_memories_by_user(client, user_id, cosmos_db_database, cosmos_db_container, return_details=False):
    """
    Retrieve all memory documents for a specific user.
    Returns a list of lists, where each inner list contains two message objects (user and assistant) representing one turn.
    If return_details=True, each turn list also includes timestamp and token counts are included in messages.
    
    Args:
        client: CosmosClient instance to use for the operation
        user_id: User ID to filter memories
        cosmos_db_database: Name of the Cosmos DB database
        cosmos_db_container: Name of the Cosmos DB container
        return_details: Whether to return detailed metadata
    """
    try:
        # Get database and container references
        database = client.get_database_client(cosmos_db_database)
        container = database.get_container_client(cosmos_db_container)
        
        # Build SELECT clause based on return_details parameter
        if return_details:
            query = """
                SELECT c.messages, c.timestamp
                FROM c
                WHERE c.user_id = @user_id AND c.type = 'memory'
                ORDER BY c.timestamp ASC
            """
        else:
            query = """
                SELECT c.messages
                FROM c
                WHERE c.user_id = @user_id AND c.type = 'memory'
                ORDER BY c.timestamp ASC
            """
        
        parameters = [
            {"name": "@user_id", "value": user_id}
        ]
        
        # Execute query
        results = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True))
        
        # Transform results into list of lists format
        # Each document has a 'messages' array with 2 elements (user and assistant)
        formatted_results = []
        for result in results:
            if 'messages' in result and len(result['messages']) == 2:
                if return_details:
                    # Include messages with token counts, plus timestamp
                    turn_data = result['messages'].copy()
                    turn_data.append({
                        "timestamp": result.get('timestamp')
                    })
                    formatted_results.append(turn_data)
                else:
                    # Strip token_count from messages
                    formatted_results.append(_strip_token_counts(result['messages']))
        
        return formatted_results
    except Exception as e:
        print(f"Warning: Failed to retrieve memories by user - {e}")
        return None


def get_memories_by_thread(client, thread_id, cosmos_db_database, cosmos_db_container, return_details=False):
    """
    Retrieve all memory documents for a specific thread.
    Returns a list of lists, where each inner list contains two message objects (user and assistant) representing one turn.
    If return_details=True, each turn list also includes timestamp and token counts are included in messages.
    
    Args:
        client: CosmosClient instance to use for the operation
        thread_id: Thread ID to filter memories
        cosmos_db_database: Name of the Cosmos DB database
        cosmos_db_container: Name of the Cosmos DB container
        return_details: Whether to return detailed metadata
    """
    try:
        # Get database and container references
        database = client.get_database_client(cosmos_db_database)
        container = database.get_container_client(cosmos_db_container)
        
        # Build SELECT clause based on return_details parameter
        if return_details:
            query = """
                SELECT c.messages, c.timestamp
                FROM c
                WHERE c.thread_id = @thread_id AND c.type = 'memory'
                ORDER BY c.timestamp ASC
            """
        else:
            query = """
                SELECT c.messages
                FROM c
                WHERE c.thread_id = @thread_id AND c.type = 'memory'
                ORDER BY c.timestamp ASC
            """
        
        parameters = [
            {"name": "@thread_id", "value": thread_id}
        ]
        
        # Execute query
        results = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False))
        
        # Transform results into list of lists format
        # Each document has a 'messages' array with 2 elements (user and assistant)
        formatted_results = []
        for result in results:
            if 'messages' in result and len(result['messages']) == 2:
                if return_details:
                    # Include messages with token counts, plus timestamp
                    turn_data = result['messages'].copy()
                    turn_data.append({
                        "timestamp": result.get('timestamp')
                    })
                    formatted_results.append(turn_data)
                else:
                    # Strip token_count from messages
                    formatted_results.append(_strip_token_counts(result['messages']))
        
        return formatted_results
    except Exception as e:
        print(f"Warning: Failed to retrieve memories by thread - {e}")
        return None


def get_summary_by_thread(client, thread_id, cosmos_db_database, cosmos_db_container, return_details=False):
    """
    Retrieve the summary document for a specific thread.
    
    Args:
        client: CosmosClient instance to use for the operation
        thread_id: Thread ID to retrieve summary for
        cosmos_db_database: Name of the Cosmos DB database
        cosmos_db_container: Name of the Cosmos DB container
        return_details: Whether to return detailed metadata
    """
    try:
        # Get database and container references
        database = client.get_database_client(cosmos_db_database)
        container = database.get_container_client(cosmos_db_container)
        
        # Build query based on return_details flag, get the latest summary
        if return_details:
            query = """
                SELECT TOP 1 c.summary, c.facts, c.thread_id, c.user_id, c.token_count, c.last_updated
                FROM c
                WHERE c.thread_id = @thread_id AND c.type = 'summary'
                ORDER BY c.last_updated DESC
            """
        else:
            query = """
                SELECT TOP 1 c.summary, c.facts
                FROM c
                WHERE c.thread_id = @thread_id AND c.type = 'summary'
                ORDER BY c.last_updated DESC
            """
        
        parameters = [
            {"name": "@thread_id", "value": thread_id}
        ]
        
        # Execute query
        results = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False))
        
        # Return the most recent summary if found
        if results:
            return results[0]
        else:
            return None
            
    except Exception as e:
        print(f"Warning: Failed to retrieve summary by thread - {e}")
        return None


def get_memory_by_id(client, item_id, cosmos_db_database, cosmos_db_container):
    """
    Retrieve a specific memory document by its ID.
    
    Args:
        client: CosmosClient instance to use for the operation
        item_id: ID of the memory document to retrieve
        cosmos_db_database: Name of the Cosmos DB database
        cosmos_db_container: Name of the Cosmos DB container
    """
    try:
        # Get database and container references
        database = client.get_database_client(cosmos_db_database)
        container = database.get_container_client(cosmos_db_container)
        
        # Query for the item by ID 
        query = "SELECT * FROM c WHERE c.id = @item_id"
        parameters = [{"name": "@item_id", "value": item_id}]
        
        results = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True))
        
        if results:
            return results[0]
        else:
            return None
    except Exception as e:
        print(f"Warning: Failed to retrieve memory by id - {e}")
        return None
