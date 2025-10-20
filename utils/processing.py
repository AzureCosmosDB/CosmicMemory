"""
Processing - Functions for processing and transforming data.
"""
import json
import uuid
import tiktoken
from datetime import datetime


def generate_embedding(openai_client, messages, openai_embedding_model, openai_embedding_dimensions):
    """
    Generate embedding vector for messages using Azure OpenAI.
    
    Args:
        openai_client: AzureOpenAI client instance to use for the operation
        messages: List of message dictionaries with 'content' field
        openai_embedding_model: Name of the embedding model to use
        openai_embedding_dimensions: Dimensions for the embedding vector
    
    Returns:
        list: Embedding vector, or None if generation failed
    """
    try:
        # Concatenate all message content for embedding
        text_to_embed = " ".join([msg.get("content", "") for msg in messages])
        
        # Generate embedding
        response = openai_client.embeddings.create(
            input=text_to_embed,
            model=openai_embedding_model,
            dimensions=openai_embedding_dimensions)
        
        return response.data[0].embedding
    except Exception as e:
        print(f"Warning: Failed to generate embedding - {e}")
        return None


def summarize_thread(openai_client, thread_memories, thread_id, user_id, openai_completions_model, openai_embedding_model, openai_embedding_dimensions, write=False):
    """
    Summarize a thread's conversation history using Azure OpenAI completions.
    
    Args:
        openai_client: AzureOpenAI client instance to use for the operation
        thread_memories: List of memory documents to summarize
        thread_id: Thread ID for the summary
        user_id: User ID for the summary
        openai_completions_model: Model to use for completions
        openai_embedding_model: Model to use for embeddings
        openai_embedding_dimensions: Dimensions for embeddings
        write: If True, generates embeddings and ID for database persistence. Default is False.
    
    Returns:
        Summary document with optional embedding and ID
    """
    try:
        # Prepare the conversation history for summarization
        conversation_text = json.dumps(thread_memories, indent=2)
        
        # System prompt for summarization
        system_prompt = """
        
        You are a conversation summarization assistant. Your job is to analyze conversation threads and extract the most relevant and important information.

        For the given conversation thread, you must:
        1. Create a concise summary of the thread that captures the main topics and outcomes
        2. Identify at least one, but no more than four key facts - these are short, important concepts or relationships (3-6 words each)
        3. Format your response as a JSON object with the following structure:

            {
            "summary": "A concise paragraph summarizing the conversation",
            "facts": ["fact 1", "fact 2", "fact 3"]
            }

        Focus on actionable information, decisions made, important context, and key relationships between entities.
"""

        # Call the completions API
        response = openai_client.chat.completions.create(
            model=openai_completions_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Summarize this conversation thread:\n\n{conversation_text}"}
            ],
            response_format={"type": "json_object"})
        
        # Parse the summary response
        summary_data = json.loads(response.choices[0].message.content)
        
        # Calculate token count for the summary
        encoding = tiktoken.get_encoding("cl100k_base")
        summary_text = summary_data.get("summary", "")
        token_count = len(encoding.encode(summary_text))
        
        # Create the base summary document
        summary_document = {
            "id": str(uuid.uuid4()),
            "thread_id": thread_id,
            "user_id": user_id,
            "type": "summary",
            "summary": summary_data.get("summary", ""),
            "facts": summary_data.get("facts", []),
            "token_count": token_count,
            "last_updated": datetime.now().isoformat() + "Z"
        }
        
        # If write is True, add embedding and id for database persistence
        if write:          
            # Combine summary and facts for embedding
            embedding_text = summary_data.get("summary", "") + " " + " ".join(summary_data.get("facts", []))
            
            # Generate embedding for the summary and facts
            embedding = generate_embedding(
                openai_client,
                [{"content": embedding_text}],
                openai_embedding_model,
                openai_embedding_dimensions)
            
            if embedding:
                summary_document["embedding"] = embedding
        
        return summary_document
        
    except Exception as e:
        print(f"Warning: Failed to summarize thread - {e}")
        return None
