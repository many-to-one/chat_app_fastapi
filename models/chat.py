# from sqlalchemy import Column, Integer, String, ForeignKey
# from sqlalchemy.orm import relationship
# from db.db import Base
# from users import User

# class Chat(Base):
#     __tablename__ = "chat"

#     id = Column(Integer, primary_key=True, index=True)
#     users_id = Column(ForeignKey("users.id", ondelete="CASCADE"))

#     user = relationship("User", back_populates="chat")