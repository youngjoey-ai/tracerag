from dotenv import load_dotenv
load_dotenv()

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 这是 Alembic 配置对象，提供对 .ini 文件中值的访问
config = context.config

# 解析配置文件以进行 Python 日志记录
# 这行代码基本上设置了日志记录器
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 在此处添加模型的 MetaData 对象
# 以支持 'autogenerate' 功能
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from app.db.base import Base
target_metadata = Base.metadata

# 配置中定义的其他值，根据 env.py 的需求，
# 可以通过以下方式获取：
# my_important_option = config.get_main_option("my_important_option")
# ... 等等


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
