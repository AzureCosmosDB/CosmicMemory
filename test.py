
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import DefaultAzureCredential
from cosmic_memory import CosmicMemory
import asyncio
import argparse
import uuid

# Create instance and configure
memory = CosmicMemory()
memory.load_config()
memory.clear_local()

system_instructions = """
        You are a helpful AI assistant. 
        Provide clear, concise, and friendly responses to user questions.
        Be conversational and helpful.
        
        You will receive relevant conversation history as context before each user message.
        Use this context to provide more informed and contextual responses.

        If the user asks what were talking about, provide an overview and summary in your own words. 

        Keep responses relatively short, no more than 50 words.

        If you need to lookup something, or the user asks you to search for something, use the semantic_retrieval tool to find relevant information.
        """


async def chat_loop(thread_id=None, user_id=None):

    # Create the agent
    print("🤖 Initializing agent...")
    # Create Azure OpenAI client with Entra ID authentication
    agent = AzureOpenAIChatClient(endpoint=memory.openai_endpoint,
                        deployment_name=memory.openai_completions_model,
                        credential=DefaultAzureCredential()).create_agent(
    instructions=system_instructions,
    name="Assistant")
     
    print("✅ Agent ready! Start chatting (type 'quit', 'exit', or 'bye' to end)\n")
    print("=" * 60)
    
    # Load existing conversation from Cosmos DB into the stack
    print(f"📥 Loading conversation history for user '{user_id}' and thread '{thread_id}' from Azure Cosmos DB...")
    existing_summary = memory.get_summary_db(thread_id, return_details=False)

    if existing_summary and 'summary' in existing_summary:
        print(f"✅ Loaded previous conversation summary")
        # Add the summary as a structured item to local memory

    else:
        print("📝 Starting new conversation (no previous history found)")
    
    print("=" * 60)
    
    # Conversation loop
    while True:
        # Get user input
        user_input = input("\n🧍 You: ").strip()
                
        # Check for exit commands
        if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
            print("\n👋 Goodbye! Chat session ended.")
            print("💾 Saving conversation to Azure Cosmos DB...")
            memory.add_local_to_db(user_id=user_id, thread_id=thread_id)
            print("✅ Conversation saved successfully!")
            break
        
        # Skip empty inputs
        if not user_input:
            continue
        
        try:

            # Get relevant memories from the stack for context
            conversation_history = memory.get_local(k=20,user_id=user_id, thread_id=thread_id)
   
            # Combine memories with user input
            combined_prompt = f"""
            Previous conversation context: {conversation_history}

            Current user message: {user_input}
            """

            # Get agent response with context
            result = await agent.run(combined_prompt)

            agent_response = str(result)
            
            # Print the response
            print(f"\n🤖 Assistant: {agent_response}")
            print("-" * 60)
            
            # Add conversation turn to memory stack
            conversation_turn = [
                {"role": "user", "content": user_input},
                {"role": "agent", "content": agent_response}
            ]
            memory.add_local(conversation_turn, user_id=user_id, thread_id=thread_id)
                        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or type 'quit' to exit.")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Chat with an AI assistant using CosmicMemory")
    parser.add_argument("-t", "--thread", dest="thread_id", default=None, help="Thread ID for the conversation (auto-generated if not provided)")
    parser.add_argument("-u", "--user", dest="user_id", default=None, help="User ID for the conversation (auto-generated if not provided)")
    
    args = parser.parse_args()
    
    # Generate GUIDs if not provided
    thread_id = args.thread_id if args.thread_id else str(uuid.uuid4())
    user_id = args.user_id if args.user_id else str(uuid.uuid4())
    
    # Print the IDs being used
    if not args.thread_id:
        print(f"📝 Generated Thread ID: {thread_id}")
    if not args.user_id:
        print(f"📝 Generated User ID: {user_id}")
    
    # Run the async chat loop with provided arguments
    asyncio.run(chat_loop(thread_id=thread_id, user_id=user_id))