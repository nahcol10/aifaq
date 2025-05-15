from utils import load_yaml_file
from main import get_ragchain
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List
from models import Session, User, Chat, Message

config_data = load_yaml_file("config.yaml")

rag_chain = get_ragchain()

# define the Query class that contains the question
class Query(BaseModel):
    text: str

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# it replies to GET requests, if the service is running
@app.get("/")
async def hello():
    return {"msg": "hello"}

# reply to POST requests: '{"text": "How to install Hyperledger fabric?"}'
@app.post("/query")
async def answer(q: Query):
    question = q.text
    result = await rag_chain.ainvoke({"input": question})

    return {"msg": result}

# New models for API  
class MessageModel(BaseModel):  
    role: str  
    content: str  
      
class ChatModel(BaseModel):  
    id: int  
    title: str  
    created_at: str  
    messages: List[MessageModel]  
  
class CreateChatRequest(BaseModel):  
    username: str  
    title: str  
  
class ChatMessageRequest(BaseModel):  
    username: str  
    chat_id: int  
    text: str  
  
# Get or create user  
def get_or_create_user(username):  
    session = Session()  
    user = session.query(User).filter_by(username=username).first()  
    if not user:  
        user = User(username=username)  
        session.add(user)  
        session.commit()  
    return user  
  
# New endpoints  
@app.post("/chats", response_model=ChatModel)  
async def create_chat(request: CreateChatRequest):  
    session = Session()  
    user = get_or_create_user(request.username)  
      
    new_chat = Chat(title=request.title, user_id=user.id)  
    session.add(new_chat)  
    session.commit()  
      
    return {  
        "id": new_chat.id,  
        "title": new_chat.title,  
        "created_at": new_chat.created_at.isoformat(),  
        "messages": []  
    }  
  
@app.get("/chats/{chat_id}", response_model=ChatModel)  
async def get_chat(chat_id: int):  
    session = Session()  
    chat = session.query(Chat).filter_by(id=chat_id).first()  
      
    if not chat:  
        return {"error": "Chat not found"}  
      
    messages = [  
        {"role": msg.role, "content": msg.content}  
        for msg in chat.messages  
    ]  
      
    return {  
        "id": chat.id,  
        "title": chat.title,  
        "created_at": chat.created_at.isoformat(),  
        "messages": messages  
    }  
  
@app.get("/users/{username}/chats")  
async def get_user_chats(username: str):  
    session = Session()  
    user = session.query(User).filter_by(username=username).first()  
      
    if not user:  
        return {"chats": []}  
      
    chats = [  
        {  
            "id": chat.id,  
            "title": chat.title,  
            "created_at": chat.created_at.isoformat()  
        }  
        for chat in user.chats  
    ]  
      
    return {"chats": chats}  
  
# Modify the existing query endpoint to save messages  
@app.post("/query")  
async def answer(q: Query):  
    question = q.text  
    result = await rag_chain.ainvoke({"input": question})  
      
    # Note: This endpoint doesn't save messages yet, will be replaced by chat_query endpoint  
      
    return {"msg": result}  
  
@app.post("/chat_query")  
async def chat_query(request: ChatMessageRequest):  
    session = Session()  
    chat = session.query(Chat).filter_by(id=request.chat_id).first()  
      
    if not chat:  
        return {"error": "Chat not found"}  
      
    # Add user message to database  
    user_message = Message(  
        content=request.text,  
        role="user",  
        chat_id=chat.id  
    )  
    session.add(user_message)  
    session.commit()  
      
    # Get the answer from the model  
    result = await rag_chain.ainvoke({"input": request.text})  
      
    # Add assistant response to database  
    assistant_message = Message(  
        content=result["answer"] if isinstance(result, dict) and "answer" in result else result,  
        role="assistant",  
        chat_id=chat.id  
    )  
    session.add(assistant_message)  
    session.commit()  
      
    return {  
        "msg": result,  
        "chat_id": chat.id  
    }

uvicorn.run(app,host=config_data["host"],port=config_data["port"])