import logging

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import router
from config import token


logging.basicConfig(level=logging.INFO)

bot = Bot(token=token, parse_mode='html')
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)
