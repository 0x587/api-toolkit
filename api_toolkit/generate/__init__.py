import datetime
import os

from api_toolkit.generate.model_metadata import ModelMetadata, LinkTableMetadata, RelationshipMetadata, RelationshipSide, FKMetadata
from api_toolkit.generate.router_metadata import RouterMetadata
from api_toolkit.generate.utils import name_convert_to_snake, plural, get_combinations
from api_toolkit.generate.mock import MockType
from api_toolkit.define.link import OneManyLink, ManyManyLink
from api_toolkit.define.model import ModelManager
from typing import Callable, Any, Sequence, Dict, List
import hashlib
from jinja2 import Environment, PackageLoader
import typer

GENERATE_FUNC = Callable[[Any, ...], str]


class CodeGenerator:
    def __init__(self, root_path='inner_code'):
        self.root_path = root_path
        self.models_path = os.path.join(root_path, 'models.py')
        self.schemas_path = os.path.join(root_path, 'schemas.py')
        self.dev_path = os.path.join(root_path, 'dev')
        self.crud_path = os.path.join(root_path, 'crud')
        self.routers_path = os.path.join(root_path, 'routers')

        if not os.path.exists(self.root_path):
            os.mkdir(self.root_path)
        if not os.path.exists(self.dev_path):
            os.mkdir(self.dev_path)
        if not os.path.exists(self.crud_path):
            os.mkdir(self.crud_path)
        if not os.path.exists(self.routers_path):
            os.mkdir(self.routers_path)
        self.env = Environment(loader=PackageLoader('api_toolkit', 'templates'))
        self.model_metadata: Dict[str, ModelMetadata] = {}
        self.link_table_metadata: List[LinkTableMetadata] = []
        self.router_metadata: List[RouterMetadata] = []
        self.mock_model_count: Dict[str, int] = {}
        self.mock_base = 10
        self.mock_relation_rate = 2

    @staticmethod
    def _check_file_valid(path):
        with open(path, 'r') as f:
            line = f.readline()
            if not line.startswith('# generate_hash:'):
                return False
            content_hash = line.split(':')[1].strip()
            f.readline()
            f.readline()
            f.readline()
            content = f.read()
            return hashlib.md5(content.encode('utf8')).hexdigest() == content_hash

    @staticmethod
    def _generate_file(path, func: GENERATE_FUNC, **kwargs):
        content = func(**kwargs)
        generate_hash = hashlib.md5(content.encode('utf8')).hexdigest()
        if os.path.exists(path):
            with open(path, 'r') as f:
                line = f.readline()
                if line.startswith('# generate_hash:'):
                    head_hash = line.split(':')[1].strip()
                else:
                    head_hash = None
                if head_hash == generate_hash and CodeGenerator._check_file_valid(path):
                    print(f'file {path} is up to date, skip generate')
                    return
                else:
                    overwrite = typer.confirm(
                        f'file {path} has been changed or is out of date, do you want to overwrite it?')
                    if not overwrite:
                        return
        with open(path, 'w') as f:
            f.write(f'# generate_hash: {generate_hash}\n')
            f.write(f'"""\n'
                    f'This file was automatically generated in {datetime.datetime.now()}\n'
                    f'"""\n')
            f.write(content)

    def _parse_mock(self):
        model_count: Dict[str, int] = {model_name: self.mock_base for model_name in self.model_metadata.keys()}
        for model_name, model in self.model_metadata.items():
            if not model.relationship:
                continue
            for relation in [r for r in model.relationship if r.side == RelationshipSide.many]:
                model_count[relation.target.name] = model_count[model_name] * self.mock_relation_rate

        if any([v > 500 for v in model_count.values()]):
            raise ValueError('too many mock model, maybe has circle relationship')

        self.mock_model_count = model_count

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

        for md in self.model_metadata.values():
            cbs = get_combinations(md.relationship)
            cb: Sequence[RelationshipMetadata]
            cbs = [{
                'combination': cb,
                'name': 'And'.join(map(lambda r: r.target.name, cb)),
                'snake_name': '_and_'.join(map(lambda r: name_convert_to_snake(r.target.name), cb))
            } for cb in cbs]
            md.relationship_combinations = cbs
        self.router_metadata = [RouterMetadata(md) for md in self.model_metadata.values()]
        self._parse_mock()

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

    def _define2router(self, metadata: RouterMetadata) -> str:
        return self.env.get_template('router.py.jinja2').render(metadata=metadata)

    def _define2crud(self, metadata: RouterMetadata) -> str:
        return self.env.get_template('crud.py.jinja2').render(metadata=metadata)

    def _router_init(self) -> str:
        return self.env.get_template('router_init.py.jinja2').render(models=self.model_metadata.values())

    def _define2mock(self) -> str:
        return self.env.get_template('mock.py.jinja2').render(
            mock_model_count=self.mock_model_count, models=self.model_metadata,
            mock_base=self.mock_base, mock_relation_rate=self.mock_relation_rate)

    def generate_routers(self):
        for metadata in self.router_metadata:
            self._generate_file(os.path.join(self.crud_path, f'{metadata.model.snake_name}_crud.py'), self._define2crud,
                                metadata=metadata)
            self._generate_file(os.path.join(self.routers_path, f'{metadata.model.snake_name}_router.py'),
                                self._define2router,
                                metadata=metadata)
        self._generate_file(os.path.join(self.routers_path, '__init__.py'), self._router_init)
        self._generate_file(os.path.join(self.crud_path, '__init__.py'), lambda: '')

    def generate_mock(self):
        self._generate_file(os.path.join(self.root_path, 'mock.py'), self._define2mock)
