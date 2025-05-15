from sqlalchemy import Column, Integer, String, Text, ForeignKey, create_engine, DateTime  
from sqlalchemy.ext.declarative import declarative_base  
from sqlalchemy.orm import sessionmaker, relationship  
import datetime  
  
Base = declarative_base()  
  
class User(Base):  
    __tablename__ = 'users'  
      
    id = Column(Integer, primary_key=True)  
    username = Column(String(50), unique=True)  
      
    chats = relationship("Chat", back_populates="user")  
  
class Chat(Base):  
    __tablename__ = 'chats'  
      
    id = Column(Integer, primary_key=True)  
    title = Column(String(100))  
    created_at = Column(DateTime, default=datetime.datetime.utcnow)  
    user_id = Column(Integer, ForeignKey('users.id'))  
      
    user = relationship("User", back_populates="chats")  
    messages = relationship("Message", back_populates="chat")  
  
class Message(Base):  
    __tablename__ = 'messages'  
      
    id = Column(Integer, primary_key=True)  
    content = Column(Text)  
    role = Column(String(20))  # 'user' or 'assistant'  
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)  
    chat_id = Column(Integer, ForeignKey('chats.id'))  
      
    chat = relationship("Chat", back_populates="messages")  
  
# Initialize the database  
engine = create_engine('sqlite:///aifaq.db')  
Base.metadata.create_all(engine)  
Session = sessionmaker(bind=engine)