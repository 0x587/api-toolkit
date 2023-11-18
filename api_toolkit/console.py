import typer

from api_toolkit.generate import CodeGenerator

from metadata import models

app = typer.Typer()


@app.command('g')
@app.command('generate')
def generate(table: bool = True, router: bool = True, mock: bool = True):
    generator = CodeGenerator()
    generator.parse_models()
    if table:
        generator.generate_tables()
    if router:
        generator.generate_routers()
    if mock:
        generator.generate_mock()


@app.command('mock')
@app.command('m')
def mock():
    from inner_code.mock import main
    main()


db_app = typer.Typer()


@db_app.command('init')
@db_app.command('i')
def db_init():
    from inner_code.dev.db import init
    init()


@db_app.command('migrate')
@db_app.command('m')
def db_migrate(msg: str = None):
    from inner_code.dev.db import migrate
    migrate(msg)


@db_app.command('upgrade')
@db_app.command('u')
def db_upgrade():
    from inner_code.dev.db import upgrade
    upgrade()


app.add_typer(db_app, name="db")
