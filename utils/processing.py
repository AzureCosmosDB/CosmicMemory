"""
Processing - Functions for processing and transforming data.
"""
import json
import tiktoken
from datetime import datetime
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
            "https://cognitiveservices.azure.com/.default")
        
        # Create Azure OpenAI client with Entra ID authentication
        client = AzureOpenAI(
            azure_endpoint=openai_endpoint,
            api_version="2024-02-01",
            azure_ad_token_provider=token_provider)
        
        # Generate embedding
        response = client.embeddings.create(
            input=text_to_embed,
            model=openai_embedding_model,
            dimensions=openai_embedding_dimensions)
        
        return response.data[0].embedding
    except Exception as e:
        print(f"Warning: Failed to generate embedding - {e}")
        return None


def summarize_thread(thread_memories, thread_id, user_id, openai_endpoint, openai_completions_model, openai_embedding_model, openai_embedding_dimensions):
    """
    Summarize a thread's conversation history using Azure OpenAI completions.
    """
    try:
        # Get Azure credential token
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default")
        
        # Create Azure OpenAI client with Entra ID authentication
        client = AzureOpenAI(
            azure_endpoint=openai_endpoint,
            api_version="2024-02-01",
            azure_ad_token_provider=token_provider)
        
        # Prepare the conversation history for summarization
        conversation_text = json.dumps(thread_memories, indent=2)
        
        # System prompt for summarization
        system_prompt = """
        
        You are a conversation summarization assistant. Your job is to analyze conversation threads and extract the most relevant and important information.

        For the given conversation thread, you must:
        1. Create a concise summary of the thread that captures the main topics and outcomes
        2. Identify key facts - these are short, important concepts or relationships (3-6 words each)
        3. Format your response as a JSON object with the following structure:

            {
            "summary": "A concise paragraph summarizing the conversation",
            "facts": ["fact 1", "fact 2", "fact 3"]
            }

        Focus on actionable information, decisions made, important context, and key relationships between entities.
"""

        # Call the completions API
        response = client.chat.completions.create(
            model=openai_completions_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Summarize this conversation thread:\n\n{conversation_text}"}
            ],
            temperature=0.3,
            response_format={"type": "json_object"})
        
        # Parse the summary response
        summary_data = json.loads(response.choices[0].message.content)
        
        # Combine summary and facts for embedding
        embedding_text = summary_data.get("summary", "") + " " + " ".join(summary_data.get("facts", []))
        
        # Generate embedding for the summary and facts
        embedding = generate_embedding(
            [{"content": embedding_text}],
            openai_endpoint,
            openai_embedding_model,
            openai_embedding_dimensions)
        
        # Calculate token count for the summary
        encoding = tiktoken.get_encoding("cl100k_base")
        summary_text = summary_data.get("summary", "")
        token_count = len(encoding.encode(summary_text))
        
        # Create the final summary document
        summary_document = {
            "thread_id": thread_id,
            "user_id": user_id,
            "summary": summary_data.get("summary", ""),
            "facts": summary_data.get("facts", []),
            "token_count": token_count,
            "embedding": embedding,
            "last_updated": datetime.now().isoformat() + "Z"
        }
        
        return summary_document
        
    except Exception as e:
        print(f"Warning: Failed to summarize thread - {e}")
        return None
