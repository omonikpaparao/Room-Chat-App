import streamlit as st
from pymongo import MongoClient
from datetime import *
import time
import certifi
st.set_page_config(page_title="OMPR Chat APP", layout="centered")
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .st-emotion-cache-1dp5vir {display: none;}
    .st-emotion-cache-18ni7ap {display: none;}
    div.stButton > button {
        background-color: #25d366 !important;
        color:black;
        border: none;
        border-radius: 10px;
        font-size: 16px;
        font-weight: bold;
        transition: background-color 0.3s ease;
        margin-top: 5px;
    }
     .message {
        padding: 8px 12px;
        margin: 5px 0;
        border-radius: 15px;
        max-width: 70%;
        display: inline-block;
        word-wrap: break-word;
        font-size: 16px;
        color:black;
    }

    /* Sent by user */
    .user {
        background-color: #dcf8c6;
        align-self: flex-end;
        text-align: left;
    }

    /* Received */
    .other {
        background-color: #ffffff;
        align-self: flex-start;
        text-align: left;
    }

    .chat-container {
        display: flex;
        flex-direction: column;
    }

    .timestamp {
        font-size: 10px;
        color: gray;
        margin-top: 2px;
    }

    </style>
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
# ---------------------- MongoDB Connection ---------------------- #
client = MongoClient(st.secrets["mongodb"]["uri"])
db = client["chat_database"]
room_meta = db["rooms"]  # Collection for storing room passwords

# ---------------------- Page Setup ---------------------- #

# ---------------------- Session State Initialization ---------------------- #
if "name" not in st.session_state:
    st.session_state.name = ""
if "room" not in st.session_state:
    st.session_state.room = ""
if "joined" not in st.session_state:
    st.session_state.joined = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_timestamp" not in st.session_state:
    st.session_state.last_timestamp = datetime.min

# ---------------------- Helper Functions ---------------------- #
def room_exists(room):
    return room_meta.find_one({"room": room}) is not None

def get_room_password(room):
    room_data = room_meta.find_one({"room": room})
    return room_data["password"] if room_data else None

def create_room(room, password):
    room_meta.insert_one({"room": room, "password": password})

def send_message(name, room, text):
    db[room].insert_one({
        "name": name,
        "text": text,
        "timestamp": datetime.utcnow()
    })
def get_new_messages(room, since):
    return list(db[room].find({"timestamp": {"$gt": since}}).sort("timestamp", 1))

# ---------------------- Room Join/Create Interface ---------------------- #
if not st.session_state.joined:
    st.title("Join or Create a Chat Room")

    with st.form("join_form"):
        name = st.text_input("Enter your Name:")
        room = st.text_input("Enter the Room Code:")
        password = st.text_input("Enter the Room Password:", type="password")
        submit = st.form_submit_button("Join")

        if submit:
            if not name or not room or not password:
                st.warning("Please fill in all fields.")
            else:
                if room_exists(room):
                    if get_room_password(room) == password:
                        st.session_state.name = name
                        st.session_state.room = room
                        st.session_state.joined = True
                        st.rerun()
                    else:
                        st.error("Room already exists, but password is incorrect.")
                else:
                    create_room(room, password)
                    st.session_state.name = name
                    st.session_state.room = room
                    st.session_state.joined = True
                    st.rerun()
    st.stop()  # Stop execution if not joined

# ---------------------- Chat UI ---------------------- #
st.title(f"Chat Room: {st.session_state.room}")
st.markdown(f"**Logged in as:** {st.session_state.name}")
# Message display area

messages_box=st.empty()
flag=0
# Display existing messages on first load
# Fetch messages on first load only
# Fetch messages on first load
if not st.session_state.messages:
    st.session_state.messages = get_new_messages(st.session_state.room, datetime.min)
    if st.session_state.messages:
        st.session_state.last_timestamp = st.session_state.messages[-1]["timestamp"]
#display messages new
with messages_box.container():
    for msg in st.session_state.messages:
        alignment = "user" if msg["name"] == st.session_state.name else "other"
        st.markdown(f"""
            <div class='chat-container'>
                <div class='message {alignment}'>
                    <b>{msg['name']}</b><br>
                    {msg['text']}
                    <div class='timestamp'>{(msg["timestamp"] + timedelta(hours=5, minutes=30)).strftime('%b %d, %Y - %I:%M %p')}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        flag=flag+1

# Message input form
with st.form("message_form", clear_on_submit=True):
    col1, col2 = st.columns([4, 1])
    with col1:
        msg = st.text_input("", placeholder="Enter Message", label_visibility="collapsed")
    with col2:
        send = st.form_submit_button("➤")
    if send and msg.strip():
        send_message(st.session_state.name, st.session_state.room, msg)

# Fetch and append only new messages
new_messages = get_new_messages(st.session_state.room, st.session_state.last_timestamp)
if new_messages:
    st.session_state.messages.extend(new_messages)
    st.session_state.last_timestamp = new_messages[-1]["timestamp"]
if(flag==0):
    time.sleep(10)
    st.rerun()
# Refresh every 2 seconds
else:
    st.rerun()
