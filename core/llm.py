from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage
from core.tools import search_museums_tool, book_ticket_tool, get_museum_details_tool

def get_agent():
    """Initializes the LLM, binds tools, and returns a LangGraph ReAct agent."""
    
    # Initialize your local model
    llm = ChatOllama(model="llama3.2", temperature=0) 
    
    # Now we have 3 tools
    tools = [search_museums_tool, book_ticket_tool, get_museum_details_tool]
    
    system_prompt = """You are a specialized and polite Museum Ticketing and Information Assistant. 
    Your ONLY purpose is to help users find museum information, get details, and book tickets using your provided tools.
    
    CRITICAL RULES:
    1. STRICT SCOPE: You must ONLY answer questions related to museums, ticketing, timings, facilities, and the specific locations in your database. 
    2. OFF-TOPIC HANDLING: If a user asks about anything unrelated to museums (e.g., coding, sports, general history not in the database, recipes, weather), you must politely decline. 
       - Use this exact phrase for off-topic questions: "I am a museum ticketing assistant and can only help you with museum information and bookings. How can I help you with your visit today?"
    3. NO HALLUCINATION: Never invent or guess information. Always use the search or details tools to verify facts.
    4. SEARCH & CONFIRMATION FIRST: Before booking or fetching details, ALWAYS use `search_museums_tool` to find the exact "Name" and "City". If multiple museums exist (e.g., "Archaeological Site Museum" in different cities), you MUST list them and ask the user to clarify which city they mean.
    5. BOOKING PROTOCOL: To book a ticket, you need the EXACT museum name, EXACT city, date (YYYY-MM-DD), and number of adults/children.
    
    Keep your answers conversational, concise, and friendly.
    """
    
    # Memory for state persistence across turns
    memory = MemorySaver()
    
    # Create the langgraph agent
    agent = create_react_agent(
        llm, 
        tools=tools, 
        prompt=system_prompt,
        checkpointer=memory
    )
    
    return agent