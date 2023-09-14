import yaml
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

with open('example.config.yaml', 'r') as file:
    config_data = yaml.safe_load(file)
    user = config_data['database']['user']
    password = config_data['database']['password']
    db_name = config_data['database']['db_name']
    host = config_data['database']['host']
    async_engine = create_async_engine(f"mysql+aiomysql://{user}:{password}@{host}/{db_name}", future=True)


async def get_async_session() -> AsyncSession:
    async_session = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
