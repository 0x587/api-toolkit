import yaml
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session

with open('config.yaml', 'r') as file:
    config_data = yaml.safe_load(file)
    user = config_data['database']['user']
    password = config_data['database']['password']
    db_name = config_data['database']['db_name']
    host = config_data['database']['host']

async_engine = create_async_engine(f"postgresql+asyncpg://{user}:{password}@{host}/{db_name}", future=True)
engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}/{db_name}", future=True)


def get_db() -> Generator[Session, None, None]:
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


async def get_async_session() -> AsyncSession:
    async_session = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
