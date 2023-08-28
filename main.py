import datetime
from typing import Optional, Type
from fastapi import FastAPI
from sqlmodel import create_engine, SQLModel, Session, Field
# from crud import SQLModelCRUDRouter

from state_item import StateBase, StateItemBase, StateItemCRUDRouter, StatusRegistrar

engine = create_engine('sqlite:///sqlite.db', echo=True)


def get_db():
    return Session(engine)


app = FastAPI()


class ProductState(StateBase):
    Order = 1  # 下单
    Produce = 2  # 生产
    Shipped = 3  # 发货
    Received = 4  # 收货


registry = StatusRegistrar(ProductState, Type["Product"])


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


api = StateItemCRUDRouter(
    registrar=registry,
    db_func=get_db,
    db_model=Product
)
app.include_router(api)

import uvicorn

SQLModel.metadata.create_all(engine)
uvicorn.run(app)

# p = Product(name="test", created_time=datetime.datetime.now(), updated_time=datetime.datetime.now())
# print(p)
# p.order_to_produce(1)
# print(p)
# p.produce_to_shipped("shanghai", "receiver")
# print(p)
# p.shipped_to_received()
# print(p)
# p.shipped_to_received()
