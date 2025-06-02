from utils import load_yaml_file
from main import get_ragchain
import streamlit as st
from menu import menu_with_redirect
from chat_history import init_db, save_message, get_messages
from query_rewriting import query_rewriting_llm

# Initialize DB
init_db()

# Redirect to app.py if not logged in
menu_with_redirect()

st.markdown("# AIFAQ")

config_path = "./config.yaml"
logo_path = "https://github.com/hyperledger-labs/aifaq/blob/mvt-streamlit/images/logo.png?raw=true"
config_data = load_yaml_file(config_path)

# filter public document in case of guest user
filter = None
if st.session_state.user_type in ['guest']:
    filter = {"access": {"$eq": "public"}}


rag_chain = get_ragchain(filter)
username = st.session_state.username

# -------------------------------
# Load user chat history from DB
# -------------------------------
if "user_messages" not in st.session_state:
    st.session_state.user_messages = {}

if username not in st.session_state.user_messages:
    messages = get_messages(username)
    if not messages:
        messages = [{"role": "assistant", "content": "How may I help you?"}]
        save_message(username, "assistant", "How may I help you?")
    st.session_state.user_messages[username] = messages

user_chat = st.session_state.user_messages[username]

# -------------------------------
# Display chat messages
# -------------------------------
for message in user_chat:
    with st.chat_message(message["role"], avatar=logo_path if message["role"] == "assistant" else None):
        st.write(message["content"])

# -------------------------------
# Handle user input
# -------------------------------
if prompt := st.chat_input():
    msg = {"role": "user", "content": prompt}
    user_chat.append(msg)
    save_message(username, "user", prompt)

    with st.chat_message("user"):
        st.write(prompt)

    # Rewrite the query for better search
    rewritten_query = query_rewriting_llm(prompt)

    with st.chat_message("assistant", avatar=logo_path):
        with st.spinner("Thinking..."):
            # Use rewritten query or original prompt based on config
            query = rewritten_query if config_data.get("use_query_rewriting", True) else prompt
            response = rag_chain.invoke({"input": query})
            # save response in a text file
            print(response, file=open('responses.txt', 'a', encoding='utf-8'))
            st.markdown(response["answer"])

        reply_msg = {"role": "assistant", "content": response["answer"]}
        user_chat.append(reply_msg)
        save_message(username, "assistant", response["answer"])
