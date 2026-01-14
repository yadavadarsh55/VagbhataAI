import streamlit as st
import uuid
import json
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.postgres import PostgresSaver

from graph import build_graph
from config import settings

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Vagbhata - Ayurvedic AI", layout="wide", initial_sidebar_state="auto")

# Custom CSS 
st.markdown("""
    <style>
    .stApp { background-color: #FCF9F1; }
    section[data-testid="stSidebar"] {
        background-color: #F5EFE1 !important;
        border-right: 1px solid #E0D5C1;
    }
    .welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding-top: 5rem;
    }
    .stButton>button {
        border-radius: 10px;
        border: 1px solid #D7CCC8;
        background-color: transparent;
        color: #5D4037;
        width: 100%;
        text-align: left;
    }
    .stChatInputContainer {
        padding-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)


# **************************************** Backend Helpers *************************

def get_all_threads():
    """Retrieves all unique thread IDs from the Postgres DB."""
    try:
        with PostgresSaver.from_conn_string(settings.database_url) as checkpointer:
            checkpointer.setup()
            checkpoints = checkpointer.list(None) 
            threads = set()
            for cp in checkpoints:
                if cp.config and 'configurable' in cp.config:
                    threads.add(cp.config['configurable'].get('thread_id'))
            return list(threads)
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return []

def get_chatbot_instance():
    """
    Creates a new instance of the chatbot with a DB connection.
    Note: Returns (chatbot_compiled, checkpointer).
    The caller must ensure the checkpointer context is managed if needed,
    but for Streamlit stateless runs, we re-initialize per run for safety.
    """
    checkpointer = PostgresSaver.from_conn_string(settings.database_url)
    graph = build_graph()
    return graph.compile(checkpointer=checkpointer)

# **************************************** Utility Functions *************************

def generate_thread_id():
    if st.user.is_logged_in:
        return st.user.name + "|" + str(uuid.uuid4())
    return str(uuid.uuid4())

def reset_chat():
    new_id = generate_thread_id()
    st.session_state['thread_id'] = new_id
    add_thread(new_id)
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if 'chat_threads' not in st.session_state:
        st.session_state['chat_threads'] = []
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    """Fetches history from the LangGraph state."""
    with PostgresSaver.from_conn_string(settings.database_url) as checkpointer:
        graph = build_graph()
        chatbot = graph.compile(checkpointer=checkpointer)
        config = {'configurable': {'thread_id': thread_id}}
        state = chatbot.get_state(config)
        return state.values.get('messages', [])

def get_thread_name(thread_id, max_length=20):
    conv = load_conversation(thread_id)
    if not conv:
        return "New Thread"
    for msg in conv:
        if isinstance(msg, HumanMessage):
            name = msg.content
            if len(name) > max_length:
                return name[:max_length].strip() + "..."
            return name
    return "New Thread"


# **************************************** Session Setup ******************************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    db_threads = get_all_threads()
    st.session_state['chat_threads'] = db_threads if db_threads else []

# Ensure current thread is in the list
add_thread(st.session_state['thread_id'])


# **************************************** Sidebar UI *********************************

st.sidebar.title('Vagbhata AI')

st.divider()

if not st.user.is_logged_in:
    st.sidebar.button("Log in with Google", on_click=st.login)

else:
    st.sidebar.markdown(f"Welcome, {st.user.name} !!!")
    st.sidebar.button("Log out", on_click=st.logout)

if st.sidebar.button("New Chat"):
    reset_chat()
    st.rerun()

st.divider()

if st.user.is_logged_in:

    st.sidebar.header('My Conversations')

    for thread_id in st.session_state['chat_threads'][::-1]:
        if st.user.name == thread_id.split('|')[0]:

            if st.sidebar.button(get_thread_name(thread_id), key=thread_id):
                st.session_state['thread_id'] = thread_id
                
                messages = load_conversation(thread_id)
                temp_messages = []
                for msg in messages:
                    if isinstance(msg, HumanMessage):
                        temp_messages.append({'role': 'user', 'content': msg.content})
                    elif isinstance(msg, AIMessage):
                        if not msg.tool_calls: 
                            temp_messages.append({'role': 'ai', 'content': msg.content})
                
                st.session_state['message_history'] = temp_messages
                st.rerun()


# *************************************** Main Chat UI ********************************

# If history is empty, show landing page
if not st.session_state['message_history']:
    st.markdown("""
        <div class="welcome-container">
            <h1 style='color: #7A4A2A; font-family: serif;'>Vagbhata</h1>
            <p style='color: #A1887F; letter-spacing: 2px;'>AYURVEDIC AI GUIDE</p>
            <img src="https://t4.ftcdn.net/jpg/03/24/52/53/240_F_324525304_yUOig2gBoxzdG7DIZCThumXmVIo7mxnb.jpg" width="150" style="margin: 20px;">
            <h2 style='color: #5D4037;'>Namaste</h2>
            <p style='color: #8D6E63; max-width: 500px;'>
                I am Vagbhata AI. Ask me about your Ayurveda, its principles or practices.
            </p>
        </div>
    """, unsafe_allow_html=True)

# Display Chat History
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.write(message['content'])

# Chat Input Processing
user_input = st.chat_input("Ask a question about Ayurveda...")

if user_input:
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.write(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}
    
    with PostgresSaver.from_conn_string(settings.database_url) as checkpointer:
        graph = build_graph()
        chatbot = graph.compile(checkpointer=checkpointer)

        with st.spinner("Responding to message..."):
            try:
                response = chatbot.invoke(
                    {'messages': [HumanMessage(content=user_input)]}, 
                    config=CONFIG
                )
                
                ai_msg_obj = response['messages'][-1]
                ai_content = ai_msg_obj.content

                if isinstance(ai_content, str) and (ai_content.startswith('{') or ai_content.startswith('[')):
                    try:
                        parsed = json.loads(ai_content)
                        if isinstance(parsed, list) and 'text' in parsed[0]:
                            ai_content = parsed[0]['text']
                    except:
                        pass 
                    
                st.session_state['message_history'].append({'role': 'ai', 'content': ai_content})
                with st.chat_message('ai'):
                    st.write(ai_content)

            except Exception as e:
                st.error(f"An error occurred: {e}")