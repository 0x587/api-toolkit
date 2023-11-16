from enum import StrEnum
from typing import Optional, List, Dict

from ..define.link import ManyManyLink
from ..define.model import Field
from .utils import plural, name_convert_to_snake

FIELD_NAME = str


class ModelMetadata:
    def __init__(self,
                 name: str,
                 fields: Dict[str, Field],
                 ):
        self.name: str = name
        self.plural_name: str = plural(name)
        self.snake_name: str = name_convert_to_snake(name)
        self.snake_plural_name: str = plural(self.snake_name)
        self.table_name: str = '__table_name_' + self.snake_name
        self.base_schema_name: str = name + 'Schema'

        self.fields: Dict[FIELD_NAME, Field] = {name: field for name, field in fields.items() if not field.primary_key}
        self.pk: Dict[FIELD_NAME, Field] = {name: field for name, field in fields.items() if field.primary_key}
        # { fk_name: pk in other table}
        self.fk: Dict[FIELD_NAME, FKMetadata] = {}

        self.relationship: List[RelationshipMetadata] = []
        self.relationship_combinations = []

    def require_one_pk(self):
        assert len(self.pk) == 1, f"model <{self.name}> must have only one pk"
        return list(self.pk.items())[0]


class LinkTableMetadata:
    def __init__(self, left: ModelMetadata, right: ModelMetadata, link: ManyManyLink):
        self.left = left
        self.right = right
        self.link = link
        self.table_name = f'link_table__{left.snake_name}__and__{right.snake_name}'
        self.left_pk_name, self.left_pk = left.require_one_pk()
        self.right_pk_name, self.right_pk = right.require_one_pk()


class RelationshipSide(StrEnum):
    # one side of 1-n relationship
    one = 'one'
    # many side of 1-n relationship
    many = 'many'
    # side of n-n relationship
    both = 'both'


class RelationshipMetadata:
    def __init__(self,
                 target: ModelMetadata,
                 side: RelationshipSide,
                 link_table: Optional[LinkTableMetadata] = None,
                 ):
        self.target: ModelMetadata = target
        self.side: RelationshipSide = side
        self.link_table: Optional[LinkTableMetadata] = link_table


class FKMetadata:
    def __init__(self, field: Field, other_model: ModelMetadata):
        self.field = field
        self.other_model = other_model

