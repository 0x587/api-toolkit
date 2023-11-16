from abc import ABC
from typing import List, Sequence, Dict, Optional
from enum import StrEnum

from .model_metadata import ModelMetadata, RelationshipMetadata, RelationshipSide
from .utils import get_combinations


class RouteMethod(StrEnum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'


class BaseRoute(ABC):
    methods: RouteMethod
    name: str
    url: str


class CreateRoute(BaseRoute):
    methods = RouteMethod.POST

    def __init__(self):
        self.name = 'create_one'
        self.url = '/create_one'


class UpdateRoute(BaseRoute):
    methods = RouteMethod.PUT

    def __init__(self):
        self.name = 'update_one'
        self.url = '/update_one'


class QueryRoute(BaseRoute):
    methods = RouteMethod.GET
    schema_suffix = ''

    def __init__(self, is_all=False, with_relation: Sequence[RelationshipMetadata] = None):
        if with_relation is None:
            with_relation = []
        self.is_all = is_all
        self.name = 'get_all' if is_all else 'get_one'
        self.url = '/get_all' if is_all else '/get_one'
        if with_relation:
            self.name += '_with_' + '_'.join([r.target.snake_name for r in with_relation])
            self.url += '_with_' + '_'.join([r.target.snake_name for r in with_relation])
            self.schema_suffix = 'With' + 'And'.join([r.target.name for r in with_relation])


class DeleteRoute(BaseRoute):
    methods = RouteMethod.DELETE

    def __init__(self, is_all=False):
        self.is_all = is_all
        self.name = 'delete_all' if is_all else 'delete_one'
        self.url = '/delete_all' if is_all else '/delete_one'


class RelationRoute(BaseRoute):
    methods = RouteMethod.POST

    def __init__(self, relation: RelationshipMetadata, is_delete=False):
        self.relation = relation
        self.is_delete = is_delete
        self.name = f'link_to_' if not is_delete else f'unlink_to_'
        self.url = f'/link_to_' if not is_delete else f'/unlink_to_'
        self.name += relation.target.snake_name
        self.url += relation.target.snake_name


class RouterMetadata:
    model: ModelMetadata
    routes: List[BaseRoute]

    def __init__(self, model: ModelMetadata):
        self.model = model
        self.routes = [
            CreateRoute(),
            UpdateRoute(),
            QueryRoute(),
            QueryRoute(is_all=True),
            DeleteRoute(),
            DeleteRoute(is_all=True)
        ]
        for relation in model.relationship:
            self.routes.append(RelationRoute(relation))
            self.routes.append(RelationRoute(relation, is_delete=True))
        for cbs in get_combinations(model.relationship):
            self.routes.append(QueryRoute(with_relation=cbs))
            self.routes.append(QueryRoute(is_all=True, with_relation=cbs))

    def query_routes(self):
        return [r for r in self.routes if isinstance(r, QueryRoute)]

    def create_routes(self):
        return [r for r in self.routes if isinstance(r, CreateRoute)]

    def update_routes(self):
        return [r for r in self.routes if isinstance(r, UpdateRoute)]

    def delete_routes(self):
        return [r for r in self.routes if isinstance(r, DeleteRoute)]

    def relation_routes(self):
        return [r for r in self.routes if isinstance(r, RelationRoute)]
