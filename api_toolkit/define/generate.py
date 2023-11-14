import datetime
import os
import re
from itertools import combinations

from .link import OneManyLink
from .model import ModelManager
from typing import Callable, Type, Any, Sequence, Dict
import hashlib
from jinja2 import Environment, PackageLoader

GENERATE_FUNC = Callable[[Any, ...], str]


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
    root_path = 'inner_code'
    models_path = os.path.join(root_path, 'models.py')
    schemas_path = os.path.join(root_path, 'schemas.py')
    dev_path = os.path.join(root_path, 'dev')
    routers_path = os.path.join(root_path, 'routers')

    def __init__(self):
        if not os.path.exists(self.root_path):
            os.mkdir(self.root_path)
        if not os.path.exists(self.dev_path):
            os.mkdir(self.dev_path)
        if not os.path.exists(self.routers_path):
            os.mkdir(self.routers_path)
        self.env = Environment(loader=PackageLoader('api_toolkit', 'templates'))
        self.models = {}

    @staticmethod
    def generate_file(path, func: GENERATE_FUNC, **kwargs):
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

    def parse_models(self, mm: Type[ModelManager]):
        models = {}
        for name, info in mm.models.items():
            model = {'name': name,
                     'plural_name': plural(name),
                     'snake_name': name_convert_to_snake(name),
                     'snake_plural_name': plural(name_convert_to_snake(name)),
                     'table_name': '__table_name_' + name_convert_to_snake(name),
                     'base_schema_name': name + 'Schema',
                     'pk': [f for f in info.fields if f['field'].primary_key][0],
                     'fields': info.fields,
                     'fk': [],
                     'relationship': [],
                     'relationship_combinations': [],
                     }

            models[name] = model
        for left, info in mm.models.items():
            if not info.links:
                continue
            for link in info.links:
                if isinstance(link, OneManyLink):
                    right = link.many
                    models[right]['fk'].append({'one_side': models[left]})
                    models[left]['relationship'].append({'target': models[right], 'type': 'many'})
                    models[right]['relationship'].append({'target': models[left], 'type': 'one'})

        def get_combinations(arr):
            result = []
            for r in range(1, len(arr) + 1):
                for combination in combinations(arr, r):
                    result.append(combination)
            return result

        for info in models.values():
            cbs = get_combinations(info['relationship'])
            cb: Sequence[Dict]
            cbs = [{
                'combination': cb,
                'name': 'And'.join(map(lambda r: r['target']['name'], cb)),
                'snake_name': '_and_'.join(map(lambda r: name_convert_to_snake(r['target']['name']), cb))
            } for cb in cbs]
            info['relationship_combinations'] = cbs
        self.models = models

    def define2table(self) -> str:
        template = self.env.get_template('models.py.jinja2')
        return template.render(models=self.models.values())

    def define2schema(self) -> str:
        template = self.env.get_template('schemas.py.jinja2')
        return template.render(models=self.models.values())

    def generate_db_script(self):
        return self.env.get_template('dev.db.py.jinja2').render()

    def generate_tables(self):
        self.parse_models(ModelManager)
        self.generate_file(self.models_path, self.define2table)
        self.generate_file(self.schemas_path, self.define2schema)
        self.generate_file(os.path.join(self.dev_path, 'db.py'), self.generate_db_script)

    def define2router(self, model) -> str:
        return self.env.get_template('router.py.jinja2').render(model=model)

    def router_init(self) -> str:
        return self.env.get_template('router_init.py.jinja2').render(models=self.models.values())

    def generate_route(self):
        # self.generate_file()
        for model in self.models.values():
            self.generate_file(os.path.join(self.routers_path, f'{model["snake_name"]}.py'),
                               self.define2router, model=model)
        self.generate_file(os.path.join(self.routers_path, '__init__.py'), self.router_init)
