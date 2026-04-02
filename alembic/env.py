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
    """在"离线"模式下运行迁移。

    此模式仅使用 URL 配置上下文，而不需要 Engine，
    尽管在这里使用 Engine 也是可以接受的。
    通过跳过 Engine 创建，我们甚至不需要 DBAPI 可用。

    在此处调用 context.execute() 会将给定的字符串输出到脚本输出。

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
    """在"在线"模式下运行迁移。

    在这种情况下，我们需要创建一个 Engine
    并将连接与上下文关联。

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
