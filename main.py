import asyncio
import logging
import re
import json

from decouple import config


from aiogram import Bot, Dispatcher, Router, types,F
from aiogram.utils import keyboard
from aiogram.filters import CommandStart, Command   
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = config("TOKEN")

dp = Dispatcher() # объект диспетчера (оброботчик событий)
bot = Bot(TOKEN)

# async - асинхронная функция (позволяет не блокировать выполнение кода)
# await - ожидание выполнения асинхронной функции

class FormRegistartion(StatesGroup):
    first_name = State()  # string
    last_name = State()   # string
    photo = State()      # file_id- string
    age = State()        #30.05.1990 - string
    phone = State()      # +380123456789 - string
    bio = State()       # string

#MENU
# 1. 📲Регистрация
mainmenu = keyboard.InlineKeyboardBuilder()
mainmenu.row(types.InlineKeyboardButton(text="📲Регистрация", callback_data="registration"))
mainmenu.row(types.InlineKeyboardButton(text="👤Користувачі", callback_data="Users"))


#users data
USER_FILE_NAME = "users.json"

def load_users():
    try:
        with open(USER_FILE_NAME, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

users = load_users()


def save_user(user):
    users.append(user)
    with open(USER_FILE_NAME, "w", encoding="utf-8") as file:
        file.write(json.dumps(users, ensure_ascii=False, indent=4))
        





    
    

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("Привіт! Я бот для реєстрації користувачів. Натисни на кнопку нижче, щоб зареєструватись"
                         ,reply_markup=mainmenu.as_markup())


@dp.callback_query(F.data == "Users")
async def users(call: types.CallbackQuery):
    users = load_users()
    if not users:
        await call.message.edit_text("Користувачі відсутні")
        return
    for user in users:
        await call.message.answer_photo(photo=user['photo'], caption=f"Ім'я: {user['first_name']}\nБіо: {user['bio']}\n\nНомер телефону: {user['phone']}")
    

@dp.callback_query(F.data == "registration")
async def registration(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(FormRegistartion.first_name)
    await call.message.edit_text("Введіть своє ім'я")

    

@dp.message(FormRegistartion.first_name)
async def first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text) # Зберігаємо дані в state
    await state.set_state(FormRegistartion.last_name) # Переходимо на наступний state
    await message.answer("Введіть своє прізвище")
    
@dp.message(FormRegistartion.last_name)
async def last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await state.set_state(FormRegistartion.photo)
    data = await state.get_data()
    full_name = f"{data['first_name']} {data['last_name']}"
    await message.answer(f"Привіт {full_name}! Тепер надішліть своє фото")
    
@dp.message(F.photo, FormRegistartion.photo)
async def photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(FormRegistartion.age)
    
    await message.answer("Введіть свій вік в форматі дд.мм.рррр\nНаприклад: 30.05.1990\nДопустимий вік від 1990 до 2015 року")
    
@dp.message(FormRegistartion.age)
async def age(message: types.Message, state: FSMContext):
    pattern = r'^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.(199\d|200\d|201[0-5])$'
    if not re.match(pattern, message.text):
        await message.answer("Введіть вік в форматі дд.мм.рррр")
        return
    
    await state.update_data(age=message.text)
    await state.set_state(FormRegistartion.phone)
    
    markup = types.ReplyKeyboardMarkup(keyboard=[
        [
            types.KeyboardButton(text="Надати номер телефону", request_contact=True)
        ]
    ])
        
    
    await message.answer("Нажміть на кнопку нижче, щоб надати доступ до свого номеру телефону"
                         ,reply_markup=markup)
    
@dp.message(F.contact, FormRegistartion.phone)
async def phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(FormRegistartion.bio)
    await message.answer("Напишіть коротко про себе")
    
@dp.message(FormRegistartion.bio)
async def bio(message: types.Message, state: FSMContext):
    await state.update_data(bio=message.text)
    data = await state.get_data()
    save_user(data)
    await state.clear()
    await message.answer(f"Дякую за реєстрацію!\n\n"
                         f"Ім'я: {data['first_name']}\n"
                         f"Прізвище: {data['last_name']}\n"
                         f"Фото: {data['photo']}\n"
                         f"Вік: {data['age']}\n"
                         f"Телефон: {data['phone']}\n"
                         f"Про себе: {data['bio']}\n"
                         f"Дані збережено"
                         )




async def main() -> None:
    await bot.set_my_commands([], scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot)


if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO)
    asyncio.run(main())