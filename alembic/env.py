import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# Добавляем путь к нашим моделям
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

try:
    # Попробуем импортировать наши модели
    from src.library_catalog.models.base import Base

    target_metadata = Base.metadata
except ImportError:
    # Если не получилось, создадим пустую метаданную
    from sqlalchemy import MetaData

    target_metadata = MetaData()
    print("Warning: Could not import models. Autogenerate might not work properly.")

config = context.config
fileConfig(config.config_file_name)


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    # Используем URL из alembic.ini
    sqlalchemy_url = config.get_main_option("sqlalchemy.url")

    # Если URL не задан в alembic.ini, попробуем получить из переменных окружения
    if not sqlalchemy_url:
        sqlalchemy_url = os.environ.get("DATABASE_URL")
        if not sqlalchemy_url:
            raise ValueError("Database URL not configured")

    connectable = create_async_engine(sqlalchemy_url)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


if context.is_offline_mode():
    # Обработка offline-режима
    print("Running in offline mode")
    # Здесь должна быть логика для offline режима
    # Но для простоты просто выходим
    sys.exit(1)
else:
    # Запускаем миграции
    asyncio.run(run_migrations_online())
