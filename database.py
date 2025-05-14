import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import pymysql

pymysql.install_as_MySQLdb()
load_dotenv()

bot_engine = create_engine(
    os.getenv("BOT_DB_URL"),
    pool_pre_ping=True,
    pool_recycle=3600
)

BotBase = declarative_base()

class Application(BotBase):
    __tablename__ = 'applications'
    
    id = Column(Integer, primary_key=True)
    region = Column(String(50))
    last_name = Column(String(100))
    first_name = Column(String(100))
    callsign = Column(String(50))
    telegram_contact = Column(String(100))
    commander_contact = Column(String(100))
    need_medicine = Column(Boolean)
    need_humanitarian_aid = Column(Boolean)
    need_equipment = Column(Boolean)

BotBase.metadata.create_all(bot_engine)
BotSessionLocal = sessionmaker(bind=bot_engine)

def get_bot_db():
    db = BotSessionLocal()
    try:
        yield db
    finally:
        db.close()
