"""
Cosmos Interface - Functions for interacting with Azure Cosmos DB and OpenAI.
"""
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceExistsError
from azure.mgmt.cosmosdb import CosmosDBManagementClient



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


def insert_memory(memory_document, cosmos_db_endpoint, cosmos_db_database, cosmos_db_container):
    """
    Insert a memory document into Cosmos DB container.
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


def semantic_search(query_embedding, k, cosmos_db_endpoint, cosmos_db_database, cosmos_db_container, return_details=False):
    """
    Find semantically similar memories using vector similarity search.
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
        
        # Build SELECT clause based on return_details parameter
        select_clause = "c.id, c.user_id, c.started_at, c.ended_at, c.messages" if return_details else "c.messages"
        
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


def recent_memories(k, cosmos_db_endpoint, cosmos_db_database, cosmos_db_container, return_details=False):
    """
    Retrieve the k most recent memory documents ordered by timestamp.
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
        
        # Build SELECT clause based on return_details parameter
        select_clause = "c.id, c.user_id, c.started_at, c.ended_at, c.messages" if return_details else "c.messages"
        
        # Query for most recent memories
        query = f"""
            SELECT TOP @k {select_clause}
            FROM c
            ORDER BY c.started_at DESC
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
    Delete a memory document from Cosmos DB by its ID.
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
        
        # First, query to get the item and its thread_id
        query = "SELECT * FROM c WHERE c.id = @item_id"
        parameters = [{"name": "@item_id", "value": item_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
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


def get_memories_by_user(user_id, cosmos_db_endpoint, cosmos_db_database, cosmos_db_container, return_details=False):
    """
    Retrieve all memory documents for a specific user.
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
        
        # Build SELECT clause based on return_details parameter
        select_clause = "c.id, c.user_id, c.started_at, c.ended_at, c.messages" if return_details else "c.messages"
        
        # Query for all memories for this user
        query = f"""
            SELECT {select_clause}
            FROM c
            WHERE c.user_id = @user_id
            ORDER BY c.started_at DESC
        """
        
        parameters = [
            {"name": "@user_id", "value": user_id}
        ]
        
        # Execute query
        results = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        return results
    except Exception as e:
        print(f"Warning: Failed to retrieve memories by user - {e}")
        return None
        
        parameters = [
            {"name": "@user_id", "value": user_id}
        ]
        
        # Execute query
        results = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        return results
    except Exception as e:
        print(f"Warning: Failed to retrieve memories by user - {e}")
        return None


def get_memories_by_thread(thread_id, cosmos_db_endpoint, cosmos_db_database, cosmos_db_container, return_details=False):
    """
    Retrieve all memory documents for a specific thread.
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
        
        # Build SELECT clause based on return_details parameter
        select_clause = "c.id, c.user_id, c.started_at, c.ended_at, c.messages" if return_details else "c.messages"
        
        # Query for all memories for this thread
        query = f"""
            SELECT {select_clause}
            FROM c
            WHERE c.thread_id = @thread_id
            ORDER BY c.started_at DESC
        """
        
        parameters = [
            {"name": "@thread_id", "value": thread_id}
        ]
        
        # Execute query
        results = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False  # Can use partition key for efficiency
        ))
        
        return results
    except Exception as e:
        print(f"Warning: Failed to retrieve memories by thread - {e}")
        return None


def get_memory_by_id(item_id, cosmos_db_endpoint, cosmos_db_database, cosmos_db_container):
    """
    Retrieve a specific memory document by its ID.
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
        
        # Query for the item by ID 
        query = "SELECT * FROM c WHERE c.id = @item_id"
        parameters = [{"name": "@item_id", "value": item_id}]
        
        results = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if results:
            return results[0]
        else:
            return None
    except Exception as e:
        print(f"Warning: Failed to retrieve memory by id - {e}")
        return None
