import datetime
import os
import re
from itertools import combinations
from enum import StrEnum

from ..define.link import OneManyLink, ManyManyLink
from ..define.model import ModelManager, Field
from typing import Callable, Any, Sequence, Dict, List, Optional
import hashlib
from jinja2 import Environment, PackageLoader

GENERATE_FUNC = Callable[[Any, ...], str]

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


def name_convert_to_snake(name: str) -> str:
    return re.sub(r'([a-z])([A-Z])', r'\1_\2', name).lower()


def plural(word: str) -> str:
    rules = [
        (r'([bcdfghjklmnpqrstvwxz])y$', r'\1ies'),
        (r'(s|x|z|ch|sh)$', r'\1es'),
        (r'([^aeiou])o$', r'\1oes'),
        (r'$', r's')
    ]

    for pattern, replacement in rules:
        if re.search(pattern, word):
            return re.sub(pattern, replacement, word)

    return word


class CodeGenerator:
    def __init__(self, root_path='inner_code'):
        self.root_path = root_path
        self.models_path = os.path.join(root_path, 'models.py')
        self.schemas_path = os.path.join(root_path, 'schemas.py')
        self.dev_path = os.path.join(root_path, 'dev')
        self.routers_path = os.path.join(root_path, 'routers')

        if not os.path.exists(self.root_path):
            os.mkdir(self.root_path)
        if not os.path.exists(self.dev_path):
            os.mkdir(self.dev_path)
        if not os.path.exists(self.routers_path):
            os.mkdir(self.routers_path)
        self.env = Environment(loader=PackageLoader('api_toolkit', 'templates'))
        self.model_metadata: Dict[str, ModelMetadata] = {}
        self.link_table_metadata: List[LinkTableMetadata] = []

    @staticmethod
    def _generate_file(path, func: GENERATE_FUNC, **kwargs):
        content = func(**kwargs)
        content_hash = hashlib.md5(content.encode('utf8')).hexdigest()
        if os.path.exists(path):
            with open(path, 'r') as f:
                line = f.readline()
                if line.startswith('# content_hash:'):
                    old_hash = line.split(':')[1].strip()
                    if old_hash == content_hash:
                        print(f'file {path} is not changed, skip generate')
                        return
        with open(path, 'w') as f:
            f.write(f'# content_hash: {content_hash}\n')
            f.write(f'"""\n'
                    f'This file was automatically generated in {datetime.datetime.now()}\n'
                    f'"""\n')
            f.write(content)

    def parse_models(self):
        mm = ModelManager
        for name, info in mm.models.items():
            self.model_metadata[name] = ModelMetadata(name, {f['name']: f['field'] for f in info.fields})
        for left_name, info in mm.models.items():
            if not info.links:
                continue
            for link in info.links:
                if isinstance(link, OneManyLink):
                    right_name = link.many
                    other_model = self.model_metadata[left_name]
                    other_pk_name, other_pk = other_model.require_one_pk()
                    fk_name = f'__fk__{other_model.snake_name}_{other_pk_name}'

                    self.model_metadata[right_name].fk[fk_name] = FKMetadata(other_pk, other_model)
                    self.model_metadata[left_name].relationship.append(
                        RelationshipMetadata(self.model_metadata[right_name], RelationshipSide.many))
                    self.model_metadata[right_name].relationship.append(
                        RelationshipMetadata(self.model_metadata[left_name], RelationshipSide.one))

                elif isinstance(link, ManyManyLink):
                    link_table = LinkTableMetadata(
                        self.model_metadata[left_name], self.model_metadata[link.right], link)
                    self.link_table_metadata.append(link_table)
                    self.model_metadata[left_name].relationship.append(
                        RelationshipMetadata(self.model_metadata[link.right], RelationshipSide.both, link_table))
                    self.model_metadata[link.right].relationship.append(
                        RelationshipMetadata(self.model_metadata[left_name], RelationshipSide.both, link_table))

        def get_combinations(arr):
            result = []
            for r in range(1, len(arr) + 1):
                for combination in combinations(arr, r):
                    result.append(combination)
            return result

        for md in self.model_metadata.values():
            cbs = get_combinations(md.relationship)
            cb: Sequence[RelationshipMetadata]
            cbs = [{
                'combination': cb,
                'name': 'And'.join(map(lambda r: r.target.name, cb)),
                'snake_name': '_and_'.join(map(lambda r: name_convert_to_snake(r.target.name), cb))
            } for cb in cbs]
            md.relationship_combinations = cbs

    def _define2table(self) -> str:
        template = self.env.get_template('models.py.jinja2')
        return template.render(models=self.model_metadata, link_tables=self.link_table_metadata)

    def _define2schema(self) -> str:
        template = self.env.get_template('schemas.py.jinja2')
        return template.render(models=self.model_metadata.values())

    def _generate_db_connect(self):
        return self.env.get_template('db.py.jinja2').render()

    def _generate_db_script(self):
        return self.env.get_template('dev.db.py.jinja2').render()

    def generate_tables(self):
        self._generate_file(os.path.join(self.root_path, 'db.py'), self._generate_db_connect)
        self._generate_file(self.models_path, self._define2table)
        self._generate_file(self.schemas_path, self._define2schema)
        self._generate_file(os.path.join(self.dev_path, 'db.py'), self._generate_db_script)

    def _define2router(self, model) -> str:
        return self.env.get_template('router.py.jinja2').render(model=model)

    def _router_init(self) -> str:
        return self.env.get_template('router_init.py.jinja2').render(models=self.model_metadata.values())

    def generate_route(self):
        for model in self.model_metadata.values():
            self._generate_file(os.path.join(self.routers_path, f'{model.snake_name}.py'), self._define2router,
                                model=model)
        self._generate_file(os.path.join(self.routers_path, '__init__.py'), self._router_init)
