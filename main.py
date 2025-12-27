from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import HumanMessage
from graph import build_graph
from config import settings

def run_bot():
    # Setup Postgres Checkpointer
    print(f"Connecting to DB at {settings.DB_HOST}...")
    
    with PostgresSaver.from_conn_string(settings.database_url) as checkpointer:
        checkpointer.setup() # Ensures tables exist
        
        # Compile the graph with the checkpointer
        graph = build_graph()
        chatbot = graph.compile(checkpointer=checkpointer)

        # Configuration for the specific conversation thread
        config = {'configurable': {'thread_id': 'thread-1'}}
        
        # User Input
        user_input = "When should I drink water?"
        print(f"User: {user_input}")

        # Invoke
        events = chatbot.invoke(
            {'messages': [HumanMessage(content=user_input)]}, 
            config=config
        )

        # Output
        last_message = events['messages'][-1].content
        print(f"Vāgbhaṭa: {last_message}")

if __name__ == "__main__":
    run_bot()