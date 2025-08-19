# app/models.py

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, Boolean, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, index=True)
    username = Column(String)
    role = Column(String, default='user')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    groups = relationship("Group", back_populates="owner")
    memberships = relationship("GroupMember", back_populates="user")
    logs = relationship("EventLog", back_populates="user")

class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    group_id = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(String, default='')
    owner_id = Column(Integer, ForeignKey('users.id'))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User", back_populates="groups")
    members = relationship("GroupMember", back_populates="group")
    messages = relationship("Message", back_populates="group")
    stats = relationship("Stats", back_populates="group")
    logs = relationship("EventLog", back_populates="group")

class GroupMember(Base):
    __tablename__ = 'group_members'
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    role = Column(String, default='member')
    joined_at = Column(DateTime, default=datetime.utcnow)
    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="memberships")
    __table_args__ = (UniqueConstraint('group_id', 'user_id', name='_group_user_uc'),)

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    content = Column(Text)
    date = Column(DateTime, default=datetime.utcnow)
    message_id = Column(String)
    is_deleted = Column(Boolean, default=False)
    is_edited = Column(Boolean, default=False)
    edit_date = Column(DateTime)
    message_type = Column(String, default='text')
    forwarded_from = Column(String)
    group = relationship("Group", back_populates="messages")
    user = relationship("User")
    links = relationship("Link", back_populates="message")
    hashtags = relationship("Hashtag", back_populates="message")

class Link(Base):
    __tablename__ = 'links'
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey('messages.id'))
    url = Column(String)
    type = Column(String)
    domain = Column(String)
    is_valid = Column(Boolean, default=True)
    message = relationship("Message", back_populates="links")

class Hashtag(Base):
    __tablename__ = 'hashtags'
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey('messages.id'))
    tag = Column(String)
    message = relationship("Message", back_populates="hashtags")

class Stats(Base):
    __tablename__ = 'stats'
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'))
    date = Column(DateTime, default=datetime.utcnow)
    hashtag_count = Column(Integer, default=0)
    link_count = Column(Integer, default=0)
    msg_count = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    group = relationship("Group", back_populates="stats")

class EventLog(Base):
    __tablename__ = 'event_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=True)
    event_type = Column(String)
    data = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="logs")
    group = relationship("Group", back_populates="logs")

class Campaign(Base):
    __tablename__ = 'campaigns'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    hashtag = Column(String)
    date_start = Column(DateTime, default=datetime.utcnow)
    date_end = Column(DateTime)

class City(Base):
    __tablename__ = 'cities'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

class Tweet(Base):
    __tablename__ = 'tweets'
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'))
    city_id = Column(Integer, ForeignKey('cities.id'))
    twitter_username = Column(String)
    city = relationship("City")
    tweet_id = Column(String)
    url = Column(String)
    datetime = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('campaign_id', 'tweet_id', name='_unique_tweet_per_campaign'),
    )

class Meta(Base):
    __tablename__ = 'meta'
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    value = Column(String)


# ---- اتصال به دیتابیس و ساخت جداول ----

from sqlalchemy import create_engine

def get_engine(db_url="sqlite:///data/telegram_stats.db"):
    return create_engine(db_url, connect_args={"check_same_thread": False})

def create_tables(engine):
    Base.metadata.create_all(engine)

def get_session(engine):
    return sessionmaker(bind=engine)()

if __name__ == "__main__":
    engine = get_engine()
    create_tables(engine)
    print("✅ دیتابیس و همه جداول با موفقیت ساخته شد!")
