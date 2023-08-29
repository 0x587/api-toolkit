from typing import Optional
from fastapi import FastAPI
from sqlmodel import create_engine, SQLModel, Session, Field

from state_item import StateBase, StateItemBase, StateItemCRUDRouter, StatusRegistrar

engine = create_engine('sqlite:///sqlite.db', echo=True)


def get_db():
    return Session(engine)


app = FastAPI()


########################################################################################################################
# define state model
class ProductState(StateBase):
    Order = 1  # 下单
    Produce = 2  # 生产
    Shipped = 3  # 发货
    Received = 4  # 收货


# define state item registrar
registry = StatusRegistrar(get_db)


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

    @registry.register(ProductState.Order, ProductState.Produce)
    def order_to_produce(self, factory_id: int):
        self.factory_id = factory_id

    @registry.register(ProductState.Produce, ProductState.Shipped)
    def produce_to_shipped(self, destination: str, receiver: str):
        self.destination = destination
        self.receiver = receiver

    @registry.register(ProductState.Shipped, ProductState.Received)
    def shipped_to_received(self):
        pass


# bind state item model to registrar
registry.bind(ProductState, Product)

# make state item api router
api = StateItemCRUDRouter(
    registrar=registry,
    db_func=get_db,
    db_model=Product,
    create_schema=ProductCreate,
)

# add state item api router to fastapi
app.include_router(api)
########################################################################################################################

# run app
import uvicorn

SQLModel.metadata.create_all(engine)
uvicorn.run(app)
