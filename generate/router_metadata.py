from abc import ABC
from typing import List, Sequence, Optional
from enum import StrEnum

from api_toolkit.generate.model_metadata import ModelMetadata, RelationshipMetadata, RelationshipSide
from api_toolkit.generate.utils import get_combinations


class RouteMethod(StrEnum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'


class BaseRoute(ABC):
    methods: RouteMethod
    name: str
    url: str
    need_crud: bool = True


class CreateRoute(BaseRoute):
    methods = RouteMethod.POST

    def __init__(self, with_relation: Optional[RelationshipMetadata] = None,
                 link_to_route: Optional['RelationRoute'] = None):
        self.name = 'create_one'
        self.url = '/create_one'
        if with_relation is None:
            with_relation = []
        if with_relation:
            self.need_crud = False
            self.relation = with_relation
            self.name += '_with_' + with_relation.target.snake_name
            self.url += '_with_' + with_relation.target.snake_name
            self.link_to_route = link_to_route


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
    create_one: CreateRoute
    update_one: UpdateRoute
    get_one: QueryRoute
    get_all: QueryRoute
    delete_one: DeleteRoute
    delete_all: DeleteRoute

    def __init__(self, model: ModelMetadata):
        self.model = model
        self.create_one = CreateRoute()
        self.update_one = UpdateRoute()
        self.get_one = QueryRoute()
        self.get_all = QueryRoute(is_all=True)
        self.delete_one = DeleteRoute()
        self.delete_all = DeleteRoute(is_all=True)
        self.routes = [
            self.create_one,
            self.update_one,
            self.get_one,
            self.get_all,
            self.delete_one,
            self.delete_all,
        ]
        for relation in model.relationship:
            if len(relation.target.pk) > 1:
                print(f"Warning: {relation.target.name} has more than one pk")
                continue
            link_to_route = RelationRoute(relation)
            self.routes.append(link_to_route)
            self.routes.append(RelationRoute(relation, is_delete=True))
            if relation.side == RelationshipSide.one:
                self.routes.append(CreateRoute(with_relation=relation, link_to_route=link_to_route))
        for cbs in get_combinations(model.relationship):
            self.routes.append(QueryRoute(with_relation=cbs))
            self.routes.append(QueryRoute(is_all=True, with_relation=cbs))

    def query_routes(self):
        return [r for r in self.routes if isinstance(r, QueryRoute) and r.need_crud]

    def create_routes(self):
        return [r for r in self.routes if isinstance(r, CreateRoute) and r.need_crud]

    def update_routes(self):
        return [r for r in self.routes if isinstance(r, UpdateRoute) and r.need_crud]

    def delete_routes(self):
        return [r for r in self.routes if isinstance(r, DeleteRoute) and r.need_crud]

    def relation_routes(self):
        return [r for r in self.routes if isinstance(r, RelationRoute) and r.need_crud]

    def link_create_routes(self):
        return [r for r in self.routes if isinstance(r, CreateRoute) and not r.need_crud]
