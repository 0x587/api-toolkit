from sqlalchemy.orm import class_mapper
from models import RateRecordDB, RateRecordSchema
from pydantic import create_model
import json

fields = {}

for field in RateRecordDB.__table__.columns:
    fields[field.name] = (field.type.python_type, ...)
mapper = class_mapper(RateRecordDB)
for field in mapper.relationships:
    fields[field.key] = (field.mapper.class_, ...)

# # 创建Pydantic模型
UserModel = create_model('UserModel', **fields)
print(json.dumps(UserModel.model_json_schema()))
