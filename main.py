from typing import Optional, List
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import create_engine, SQLModel, Session, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from auth.models import (BaseUser, BaseUserCreate, BaseUserUpdate, BaseUserDB,
                         BaseGroup, BaseGroupCreate, BaseGroupUpdate, BaseGroupDB)
from auth.config import AuthConfigBase
from state_item import StateBase, StateItemBase, StateItemCRUDRouter, StatusRegistrar

from auth import AuthFactory

user = 'main'
password = 'YFZc6rfS5TjXH2kH'
db_name = 'main'
host = '8.134.109.183'

engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}/{db_name}")
async_engine = create_async_engine(f"mysql+aiomysql://{user}:{password}@{host}/{db_name}", future=True)


async def create_db_and_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_async_session() -> AsyncSession:
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


def get_db():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


app = FastAPI()


########################################################################################################################


class Config(AuthConfigBase):
    class User(BaseUser):
        name: int

    class UserCreate(BaseUserCreate):
        name: int

    class UserUpdate(BaseUserUpdate):
        name: Optional[int]

    class UserDB(BaseUserDB, table=True):
        name: int

    class Group(BaseGroup):
        name: str

    class GroupCreate(BaseGroupCreate):
        name: str

    class GroupUpdate(BaseGroupUpdate):
        name: str

    class GroupDB(BaseGroupDB, table=True):
        name: str


auth = AuthFactory(Config)(get_async_session, 'secret')
app.include_router(auth.router)


@app.get('/hello')
async def test(u: Config.UserDB = Depends(auth.current_user),
               g: Config.GroupDB = Depends(auth.current_group),
               gs: List[Config.GroupDB] = Depends(auth.own_groups)):
    return {
        'user': u,
        'group': g,
        'groups': gs
    }


########################################################################################################################
# define state model
class ProductState(StateBase):
    Order = 1  # 下单
    Produce = 2  # 生产
    Shipped = 3  # 发货
    Received = 4  # 收货
    Missed = 5  # 丢失


# define state item registrar
registry = StatusRegistrar(get_db, app)


# define state item model
class ProductCreate(SQLModel):
    name: str


# define state item model
class Product(StateItemBase, table=True):
    id: Optional[int] = Field(primary_key=True)
    state: ProductState = Field(index=True, default=ProductState.Order)
    name: str
    factory_id: Optional[int]
    destination: Optional[str]
    receiver: Optional[str]

    @registry.register(ProductState.Order, ProductState.Produce, 'make product')
    def order_to_produce(self, factory_id: int):
        self.factory_id = factory_id

    @registry.register(ProductState.Produce, ProductState.Shipped, 'deliver')
    def produce_to_shipped(self, destination: str, receiver: str):
        self.destination = destination
        self.receiver = receiver

    @registry.register(ProductState.Shipped, ProductState.Received, 'receive')
    def shipped_to_received(self):
        pass

    @registry.register(ProductState.Shipped, ProductState.Missed, 'miss')
    def shipped_to_missed(self):
        pass

    @registry.register(ProductState.Missed, ProductState.Received, 'receive')
    def missed_to_received(self):
        pass


# bind state item model to registrar
registry.bind(ProductState, Product)

# make state item api _router
api = StateItemCRUDRouter(
    registrar=registry,
    db_func=get_db,
    db_model=Product,
    create_schema=ProductCreate,
)

# add state item api _router to fastapi
app.include_router(api)

########################################################################################################################


# run app
import uvicorn


@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()


uvicorn.run(app)
