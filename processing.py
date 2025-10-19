"""
Processing - Functions for processing and transforming data.
"""
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider


def generate_embedding(messages, openai_endpoint, openai_embedding_model, openai_embedding_dimensions):
    """
    Generate embedding vector for messages using Azure OpenAI.
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
