from typing import Optional
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import create_engine, SQLModel, Session, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from state_item import StateBase, StateItemBase, StateItemCRUDRouter, StatusRegistrar

from auth import AuthFactory

engine = create_engine('sqlite:///sqlite.db')
async_engine = create_async_engine("sqlite+aiosqlite:///sqlite.db", future=True)


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

from auth.config import AuthConfig

auth = AuthFactory(AuthConfig())(get_async_session, 'secret')
app.include_router(auth.router)

########################################################################################################################
# run app
import uvicorn


@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()


uvicorn.run(app)
