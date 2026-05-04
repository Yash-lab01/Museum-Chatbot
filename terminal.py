import time
from core.llm import get_agent

def main():
    print("Initializing Museum Bot...")
    # Get the LangGraph agent
    agent = get_agent()
    
    # We use a static thread_id for this terminal session to persist memory
    config = {"configurable": {"thread_id": "terminal_session_1"}}
    
    print("\n🤖 Museum Bot Ready. Type 'exit' to quit.\n" + "-"*40)
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
            
        try:
            # 1. Start the timer right before the agent starts thinking
            start_time = time.perf_counter()
            
            # 2. Invoke the agent. LangGraph manages the history natively!
            response = agent.invoke(
                {"messages": [("user", user_input)]}, 
                config=config
            )
            
            # 3. Stop the timer right after it finishes
            end_time = time.perf_counter()
            
            # 4. Calculate the difference
            elapsed_time = end_time - start_time
            
            # The response["messages"] list contains all history. The last one is the bot's response.
            bot_response = response["messages"][-1].content
            print(f"\nBot: {bot_response}")
            
            # 5. Print the timer cleanly below the response
            print(f"\n⏱️  [Response generated in {elapsed_time:.2f} seconds]")
            
        except Exception as e:
            print(f"\n[Error]: {e}")

if __name__ == "__main__":
    main()