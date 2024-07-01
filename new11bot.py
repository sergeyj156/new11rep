import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
import sqlite3
import random
import pandas as pd

# Установка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
API_TOKEN = '7152142719:AAEt-5t-ulWhc-BH_Szk5-zF46rgva-1FZA'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
storage = MemoryStorage()  # Инициализация MemoryStorage
dp = Dispatcher(bot, storage=storage)
ADMIN_ID = [679030634, 927878071]

# Подключение к базе данных SQLite
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Подключение к базе данных SQLite
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Создание таблицы пользователей (если не существует)
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    points INTEGER DEFAULT 0
)''')

# Создание таблицы для кодовых слов (если не существует)
cursor.execute('''CREATE TABLE IF NOT EXISTS codewords (
    code TEXT PRIMARY KEY,
    points INTEGER
)''')

# Создание таблицы для реферальных ссылок (если не существует)
cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (
    user_id INTEGER,
    referral_code TEXT,
    points INTEGER DEFAULT 150,
    invited_user_id INTEGER,
    status TEXT DEFAULT 'pending'
)''')

# Создание таблицы для кодовых слов пользователей (если не существует)
cursor.execute('''CREATE TABLE IF NOT EXISTS user_codewords (
    user_id INTEGER,
    code TEXT
)''')

# Создание таблицы для ответов пользователей (если не существует)
cursor.execute('''CREATE TABLE IF NOT EXISTS user_answers (
    user_id INTEGER,
    question TEXT,
    answer TEXT
)''')
conn.commit()

# Создание кнопок меню
menu_markup = InlineKeyboardMarkup(row_width=2)
menu_markup.add(
    InlineKeyboardButton('Правила игры 🤓', callback_data='rules'),
    InlineKeyboardButton('Каналы и чаты для участия', callback_data='channels'),
    InlineKeyboardButton('Мои баллы', callback_data='points'),
    InlineKeyboardButton('Рейтинг 🔥', callback_data='rating'),
    InlineKeyboardButton('Получить баллы', callback_data='get_points'),
    InlineKeyboardButton('Ачивки месяца 🎁', callback_data='achievements'),
    InlineKeyboardButton('Помощь', callback_data='help'),
    InlineKeyboardButton('100балльный мэтч ❤️', callback_data='match')
)

# Словарь для хранения идентификаторов сообщений
user_message_ids = {}


# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer("Хэй! Ты попал в меню бота Летнего лагеря 100балльного репетитора ☀️\n\n"
                         "Ниже кнопки для навигации, чтобы ты быстрее включился в игру\n\n"
                         "Удачи 😉\n\n"
                         "Важно! Перед стартом проверь, чтобы в твоём профиле был юзернейм, т.е. тебя можно было найти в телеграм через «@». "
                         "Это важно для связи и получения приза в конце месяца", reply_markup=menu_markup)


# Обработчики кнопок меню
@dp.callback_query_handler(lambda c: c.data == 'rules')
async def show_rules(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    media = []
    files = []
    for i in range(1, 6):
        file = open(f'foto_lee/{i}.jpg', 'rb')
        files.append(file)
        media.append(InputMediaPhoto(file))

    message_ids = []

    # Отправка медиа-группы (фотографий)
    media_messages = await bot.send_media_group(callback_query.from_user.id, media)
    for msg in media_messages:
        message_ids.append(msg.message_id)

    # Закрытие файлов
    for file in files:
        file.close()

    # Отправка текста
    rules_message = await bot.send_message(callback_query.from_user.id,
                                           "В карточках можешь чекнуть основные правила игры!\n\n"
                                           "Если возникнут вопросы, переходи в раздел «помощь». Менеджер подключится и поможет со всем разобраться 🥰",
                                           reply_markup=InlineKeyboardMarkup().add(
                                               InlineKeyboardButton("Вернуться назад", callback_data='main_menu')))
    message_ids.append(rules_message.message_id)

    # Сохранение идентификаторов сообщений для удаления
    user_message_ids[callback_query.from_user.id] = message_ids


@dp.callback_query_handler(lambda c: c.data == 'channels')
async def show_channels(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    channel_message = await bot.send_message(callback_query.from_user.id,
                                             "Собрали каналы и чаты Летнего лагеря, в которых проходит игра на активность 👇🏼\n\n"
                                             "Выбирай подходящие и вступай!",
                                             reply_markup=InlineKeyboardMarkup().add(
                                                 InlineKeyboardButton("Каналы и чаты",
                                                                      url='https://t.me/addlist/4hAmIl92dFk1MTQ6')
                                             ).add(InlineKeyboardButton("Вернуться назад", callback_data='main_menu')))

    # Сохранение идентификаторов сообщений для удаления
    user_message_ids[callback_query.from_user.id] = [channel_message.message_id]


@dp.callback_query_handler(lambda c: c.data == 'points')
async def show_points(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    cursor.execute("SELECT points FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        points = result[0]
    else:
        points = 0
        cursor.execute("INSERT INTO users (id, username, points) VALUES (?, ?, ?)",
                       (user_id, callback_query.from_user.username, points))
        conn.commit()

    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    if points == 0:
        points_message = await bot.send_message(callback_query.from_user.id, "У тебя пока 0 баллов\n\n"
                                                                             "Залетай в каналы и чаты для участия и будь активным, чтобы стать лидером месяца и забрать топовый приз",
                                                reply_markup=InlineKeyboardMarkup().add(
                                                    InlineKeyboardButton("Вернуться назад", callback_data='main_menu')))
    else:
        points_message = await bot.send_message(callback_query.from_user.id, f"На твоём счету уже {points} баллов 😉\n\n"
                                                                             "Продолжай в том же темпе, чтобы в конце месяца получить топовый приз",
                                                reply_markup=InlineKeyboardMarkup().add(
                                                    InlineKeyboardButton("Вернуться назад", callback_data='main_menu')))

    # Сохранение идентификаторов сообщений для удаления
    user_message_ids[callback_query.from_user.id] = [points_message.message_id]


@dp.callback_query_handler(lambda c: c.data == 'rating')
async def show_rating(callback_query: types.CallbackQuery):
    cursor.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 10")
    results = cursor.fetchall()

    if results:
        leaderboard = "Рейтинг лидеров:\n\n"
        for i, (username, points) in enumerate(results, start=1):
            leaderboard += f"{i}. {username} - {points} баллов\n"
    else:
        leaderboard = "Рейтинг пока пуст"

    cursor.execute("SELECT COUNT(*) FROM users WHERE points > (SELECT points FROM users WHERE id = ?)",
                   (callback_query.from_user.id,))
    position = cursor.fetchone()[0] + 1

    leaderboard += f"\nСейчас ты на {position} месте!"

    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    rating_message = await bot.send_message(callback_query.from_user.id, leaderboard,
                                            reply_markup=InlineKeyboardMarkup().add(
                                                InlineKeyboardButton("Вернуться назад", callback_data='main_menu')))

    # Сохранение идентификаторов сообщений для удаления
    user_message_ids[callback_query.from_user.id] = [rating_message.message_id]


@dp.callback_query_handler(lambda c: c.data == 'main_menu')
async def process_callback_button_main_menu(callback_query: types.CallbackQuery):
    message_ids = user_message_ids.get(callback_query.from_user.id, [])
    for msg_id in message_ids:
        await bot.delete_message(callback_query.from_user.id, msg_id)
    await bot.send_message(callback_query.from_user.id, "Хэй! Ты попал в меню бота Летнего лагеря 100балльного репетитора ☀️\n\n"
                         "Ниже кнопки для навигации, чтобы ты быстрее включился в игру\n\n"
                         "Удачи 😉\n\n"
                         "Важно! Перед стартом проверь, чтобы в твоём профиле был юзернейм, т.е. тебя можно было найти в телеграм через «@». "
                         "Это важно для связи и получения приза в конце месяца", reply_markup=menu_markup)


# Обработчик кнопки "Получить баллы"
@dp.callback_query_handler(lambda c: c.data == 'get_points')
async def get_points(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    points_markup = InlineKeyboardMarkup(row_width=1)
    points_markup.add(
        InlineKeyboardButton('Отправить кодовое', callback_data='send_codeword'),
        InlineKeyboardButton('Отправить пост', callback_data='send_post'),
        InlineKeyboardButton('Пригласить друга', callback_data='invite_friend'),
        InlineKeyboardButton('Вернуться назад', callback_data='main_menu')
    )

    points_message = await bot.send_message(callback_query.from_user.id, "Выбери один из вариантов:",
                                            reply_markup=points_markup)
    user_message_ids[callback_query.from_user.id] = [points_message.message_id]


# Обработчики для подменю "Получить баллы"
@dp.callback_query_handler(lambda c: c.data == 'send_codeword')
async def send_codeword(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    codeword_markup = InlineKeyboardMarkup(row_width=1)
    codeword_markup.add(
        InlineKeyboardButton('Выполнить задание', callback_data='execute_task'),
        InlineKeyboardButton('Вернуться назад', callback_data='get_points')
    )

    codeword_message = await bot.send_message(callback_query.from_user.id,
                                              "Чтобы получить баллы за выполнение задания или просмотр веба, отправь кодовое слово в ответ на это сообщение 👇🏼",
                                              reply_markup=codeword_markup)
    user_message_ids[callback_query.from_user.id] = [codeword_message.message_id]

@dp.callback_query_handler(lambda c: c.data == 'execute_task')
async def execute_task(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    # Ожидание кодового слова
    @dp.message_handler()
    async def check_codeword(message: types.Message):
        user_id = message.from_user.id
        codeword = message.text

        cursor.execute("SELECT points FROM codewords WHERE code = ?", (codeword,))
        result = cursor.fetchone()

        if result:
            points = result[0]
            cursor.execute("SELECT COUNT(*) FROM user_codewords WHERE user_id = ? AND code = ?", (user_id, codeword))
            count = cursor.fetchone()[0]

            if count == 0:
                cursor.execute("INSERT INTO user_codewords (user_id, code) VALUES (?, ?)", (user_id, codeword))
                cursor.execute("UPDATE users SET points = points + ? WHERE id = ?", (points, user_id))
                conn.commit()
                await message.reply(f"Кодовое слово '{codeword}' принято! Ты получил {points} баллов.",
                                    reply_markup=InlineKeyboardMarkup().add(
                                        InlineKeyboardButton("Вернуться назад", callback_data='main_menu')))
            else:
                await message.reply("Ты уже использовал это кодовое слово.",
                                    reply_markup=InlineKeyboardMarkup().add(
                                        InlineKeyboardButton("Вернуться назад", callback_data='main_menu')))
        else:
            await message.reply("Неверное кодовое слово. Попробуй снова.",
                                reply_markup=InlineKeyboardMarkup().add(
                                    InlineKeyboardButton("Вернуться назад", callback_data='main_menu')))

    execute_task_message = await bot.send_message(callback_query.from_user.id, "Ожидаю кодовое слово...")
    user_message_ids[callback_query.from_user.id] = [execute_task_message.message_id]


# Обработчик для кнопки "send_post"
# Обработчик для кнопки "send_post"
@dp.callback_query_handler(lambda c: c.data == 'send_post')
async def send_post(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    with open('foto_lee/7.jpg', 'rb') as photo:  # Замените 'path_to_image.jpg' на путь к вашему изображению
        post_message = await bot.send_photo(callback_query.from_user.id, photo,
                                            caption="Чтобы получить баллы за пост, изучи правила в карточке 😉\n\n"
                                                    "Если твой пост соответствует требованиям, отправляй скриншот поста, ссылку на него и хэштег #100балльныйрепетитор!",
                                            reply_markup=InlineKeyboardMarkup().add(
                                                InlineKeyboardButton("Вернуться назад", callback_data='main_menu')))
    user_message_ids[callback_query.from_user.id] = [post_message.message_id]

# Обработчик для получения фото и текста от пользователя
@dp.message_handler(content_types=['photo'])
async def handle_post(message: types.Message):
    user_info = f"Пользователь: @{message.from_user.username} (ID: {message.from_user.id})"
    caption = f"{user_info}\n\n{message.caption}" if message.caption else user_info

    photo = message.photo[-1].file_id

    for admin_id in ADMIN_ID:
        await bot.send_photo(admin_id, photo, caption=caption)

    await message.reply("Фото и текст отправлены администратору.", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("Вернуться назад", callback_data='main_menu')))

# Обработчик для кнопки "Вернуться назад"
@dp.callback_query_handler(lambda c: c.data == 'main_menu')
async def process_callback_button_main_menu(callback_query: types.CallbackQuery):
    message_ids = user_message_ids.get(callback_query.from_user.id, [])
    for msg_id in message_ids:
        await bot.delete_message(callback_query.from_user.id, msg_id)

    await bot.send_message(callback_query.from_user.id, "Возвращаемся в меню", reply_markup=get_admin_markup())
@dp.callback_query_handler(lambda c: c.data == 'invite_friend')
async def invite_friend(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
    invite_markup = InlineKeyboardMarkup(row_width=1)
    invite_markup.add(
        InlineKeyboardButton('Сгенерировать ссылку', callback_data='generate_link'),
        InlineKeyboardButton('Вернуться назад', callback_data='get_points')
    )

    invite_message = await bot.send_message(callback_query.from_user.id, "Чтобы получить баллы, сгенерируй ссылку и отправь её другу.\n\n"
                                                                        "Важно! Баллы сохранятся на твоём счету, если друг не отпишется от каналов в течение 3-х дней.",
                                            reply_markup=invite_markup)
    user_message_ids[callback_query.from_user.id] = [invite_message.message_id]

@dp.callback_query_handler(lambda c: c.data == 'generate_link')
async def generate_link(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
    referral_code = f"ref-{random.randint(1000, 9999)}"
    cursor.execute("INSERT INTO referrals (user_id, referral_code) VALUES (?, ?)", (callback_query.from_user.id, referral_code))
    conn.commit()

    link_message = await bot.send_message(callback_query.from_user.id, f"Вот твоя ссылка для приглашения в каналы: https://t.me/tutor_100ballniy_camp_bot?start={referral_code}\n\n"
                                                                      "Её можно отправлять неограниченное количество раз 😉\n\n"
                                                                      "Как только друг перейдёт по ссылке, бот автоматически начислит тебе баллы.",
                                         reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("Вернуться назад", callback_data='main_menu')))
    user_message_ids[callback_query.from_user.id] = [link_message.message_id]

@dp.message_handler(commands=['start'])
async def referral_start(message: types.Message):
    if len(message.text.split()) > 1:
        referral_code = message.text.split()[1]
        user_id = message.from_user.id
        cursor.execute("SELECT user_id FROM referrals WHERE referral_code = ?", (referral_code,))
        result = cursor.fetchone()

        if result:
            referrer_id = result[0]
            cursor.execute("UPDATE users SET points = points + 150 WHERE id = ?", (referrer_id,))
            cursor.execute(
                "INSERT INTO users (id, username, points) VALUES (?, ?, 150) ON CONFLICT(id) DO UPDATE SET points = points + 150",
                (user_id, message.from_user.username))
            cursor.execute("UPDATE referrals SET invited_user_id = ?, status = 'accepted' WHERE referral_code = ?",
                           (user_id, referral_code))
            conn.commit()
            await message.reply(f"Ты был приглашён! На твой счёт добавлено 150 баллов.", reply_markup=menu_markup)
        else:
            await message.reply("Неверная реферальная ссылка.", reply_markup=menu_markup)
    else:
        await send_welcome(message)


@dp.callback_query_handler(lambda c: c.data == 'achievements')
async def show_achievements(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    # Путь к изображению
    image_path = 'foto_lee/6.jpg'  # Замените на реальный путь к изображению

    # Отправка изображения и текста
    with open(image_path, 'rb') as photo:
        achievements_message = await bot.send_photo(
            callback_query.from_user.id,
            photo,
            caption="Гонка за призами этого месяца в самом разгаре!\n\n"
                    "Чекай карточку, чтобы узнать, какие призы тебя ждут в июле 🔥",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("Вернуться назад", callback_data='main_menu')
            )
        )

    user_message_ids[callback_query.from_user.id] = [achievements_message.message_id]


@dp.callback_query_handler(lambda c: c.data == 'help')
async def show_help(callback_query: types.CallbackQuery):
    await bot.send_message(
        callback_query.from_user.id,
        "Пожалуйста, опиши свою проблему, чтобы менеджер быстрее нашёл решение",
        reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("Вернуться назад", callback_data='main_menu'))
    )

    @dp.message_handler()
    async def handle_help_message(message: types.Message):
        for admin_id in ADMIN_ID:
            try:
                await bot.send_message(admin_id,
                                       f"Сообщение от пользователя @{message.from_user.username}:\n\n{message.text}")
            except aiogram.utils.exceptions.ChatNotFound:
                logging.error(f"Chat with admin_id {admin_id} not found")
        await message.reply("Спасибо! Менеджер скоро подключится и поможет разобраться 🤓",
                            reply_markup=InlineKeyboardMarkup().add(
                                InlineKeyboardButton("Вернуться назад", callback_data='main_menu')))

        # Удаление обработчика после получения сообщения
        dp.message_handlers.unregister(handle_help_message)


@dp.callback_query_handler(lambda c: c.data == 'main_menu')
async def process_callback_button_main_menu(callback_query: types.CallbackQuery):
    await bot.send_message(
        callback_query.from_user.id,
        "Возвращаемся в меню",
        reply_markup=menu_markup
    )
    # Удаление обработчика сообщения при возвращении в главное меню
    dp.message_handlers.unregister(handle_help_message)

@dp.callback_query_handler(lambda c: c.data == 'main_menu')
async def process_callback_button_main_menu(callback_query: types.CallbackQuery):
    message_ids = user_message_ids.get(callback_query.from_user.id, [])
    for msg_id in message_ids:
        await bot.delete_message(callback_query.from_user.id, msg_id)
    await bot.send_message(callback_query.from_user.id, "Возвращаемся в меню", reply_markup=menu_markup)

# Обработчик для кнопки "100балльный мэтч ❤️"
@dp.callback_query_handler(lambda c: c.data == 'match')
async def show_match(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    match_markup = InlineKeyboardMarkup(row_width=1)
    match_markup.add(
        InlineKeyboardButton('Рассказать о себе', callback_data='tell_about_yourself'),
        InlineKeyboardButton('Найти друга', callback_data='start_search'),
        InlineKeyboardButton('Вернуться назад', callback_data='main_menu')
    )

    match_message = await bot.send_message(callback_query.from_user.id,
                                           "«100балльный мэтч» — это крутая фича в боте, с помощью которой ты сможешь найти классных друзей!\n\n"
                                           "Заполняй анкету перед поиском, а затем генерируй список 👇🏼\n\n"
                                           "P. S. За эту активность баллы не начисляются",
                                           reply_markup=match_markup)
    user_message_ids[callback_query.from_user.id] = [match_message.message_id]

# Обработчик для кнопки "рассказать о себе"
@dp.callback_query_handler(lambda c: c.data == 'tell_about_yourself')
async def tell_about_yourself(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    start_test_markup = InlineKeyboardMarkup(row_width=1)
    start_test_markup.add(
        InlineKeyboardButton('Начать тест', callback_data='start_test'),
        InlineKeyboardButton('Вернуться назад', callback_data='main_menu')
    )

    start_test_message = await bot.send_message(callback_query.from_user.id,
                                                "Супер!\n\n"
                                                "Сейчас тебе предстоит ответить на несколько вопросов. На основе ответов бот найдёт ребят, с которыми у вас точно мэтч ❤️\n\n"
                                                "Если ты уже прошел тест, то вернись назад и тыкни на кнопку «найти друга»",
                                                reply_markup=start_test_markup)
    user_message_ids[callback_query.from_user.id] = [start_test_message.message_id]

# Обработчики для теста
@dp.callback_query_handler(lambda c: c.data == 'start_test')
async def start_test(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    age_markup = InlineKeyboardMarkup(row_width=1)
    age_markup.add(
        InlineKeyboardButton('17 и больше', callback_data='age_17_18'),
        InlineKeyboardButton('14-16', callback_data='age_14_16'),
        InlineKeyboardButton('13 и меньше', callback_data='age_13')
    )

    age_message = await bot.send_message(callback_query.from_user.id, "Сколько тебе лет?", reply_markup=age_markup)
    user_message_ids[callback_query.from_user.id] = [age_message.message_id]

# Обработчики для вопросов анкеты
@dp.callback_query_handler(lambda c: c.data.startswith('age_'))
async def handle_age(callback_query: types.CallbackQuery):
    age = callback_query.data.split('_')[1]
    user_id = callback_query.from_user.id

    # Сохранение ответа в базу данных
    cursor.execute("INSERT INTO user_answers (user_id, question, answer) VALUES (?, ?, ?)", (user_id, 'age', age))
    conn.commit()

    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    class_markup = InlineKeyboardMarkup(row_width=1)
    class_markup.add(
        InlineKeyboardButton('11 или выпускник', callback_data='class_11'),
        InlineKeyboardButton('10', callback_data='class_10'),
        InlineKeyboardButton('9', callback_data='class_9'),
        InlineKeyboardButton('8 и ниже', callback_data='class_8')
    )

    class_message = await bot.send_message(callback_query.from_user.id, "Супер! В какой класс переходишь?", reply_markup=class_markup)
    user_message_ids[callback_query.from_user.id] = [class_message.message_id]

@dp.callback_query_handler(lambda c: c.data.startswith('class_'))
async def handle_class(callback_query: types.CallbackQuery):
    class_num = callback_query.data.split('_')[1]
    user_id = callback_query.from_user.id

    # Сохранение ответа в базу данных
    cursor.execute("INSERT INTO user_answers (user_id, question, answer) VALUES (?, ?, ?)", (user_id, 'class', class_num))
    conn.commit()

    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    direction_markup = InlineKeyboardMarkup(row_width=1)
    direction_markup.add(
        InlineKeyboardButton('Естественно-научное', callback_data='direction_natural'),
        InlineKeyboardButton('Гуманитарное', callback_data='direction_humanitarian'),
        InlineKeyboardButton('Техническое', callback_data='direction_technical'),
        InlineKeyboardButton('Я ещё в поиске себя', callback_data='direction_searching')
    )

    direction_message = await bot.send_message(callback_query.from_user.id, "Агаа! Теперь выбери подходящее направление", reply_markup=direction_markup)
    user_message_ids[callback_query.from_user.id] = [direction_message.message_id]

@dp.callback_query_handler(lambda c: c.data.startswith('direction_'))
async def handle_direction(callback_query: types.CallbackQuery):
    direction = callback_query.data.split('_')[1]
    user_id = callback_query.from_user.id

    # Сохранение ответа в базу данных
    cursor.execute("INSERT INTO user_answers (user_id, question, answer) VALUES (?, ?, ?)", (user_id, 'direction', direction))
    conn.commit()

    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    hobbies_markup = InlineKeyboardMarkup(row_width=1)
    hobbies_markup.add(
        InlineKeyboardButton('Кино, сериалы', callback_data='hobby_movies'),
        InlineKeyboardButton('Книги', callback_data='hobby_books'),
        InlineKeyboardButton('Игры', callback_data='hobby_games'),
        InlineKeyboardButton('Ничего из перечисленного', callback_data='hobby_none')
    )

    hobbies_message = await bot.send_message(callback_query.from_user.id, "Что выберешь из перечисленного?", reply_markup=hobbies_markup)
    user_message_ids[callback_query.from_user.id] = [hobbies_message.message_id]

@dp.callback_query_handler(lambda c: c.data.startswith('hobby_'))
async def handle_hobby(callback_query: types.CallbackQuery):
    hobby = callback_query.data.split('_')[1]
    user_id = callback_query.from_user.id

    # Сохранение ответа в базу данных
    cursor.execute("INSERT INTO user_answers (user_id, question, answer) VALUES (?, ?, ?)", (user_id, 'hobby', hobby))
    conn.commit()

    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    night_owl_markup = InlineKeyboardMarkup(row_width=1)
    night_owl_markup.add(
        InlineKeyboardButton('Сова (активный ночью)', callback_data='night_owl'),
        InlineKeyboardButton('Жаворонок (активный утром)', callback_data='early_bird')
    )

    night_owl_message = await bot.send_message(callback_query.from_user.id, "Ты больше...", reply_markup=night_owl_markup)
    user_message_ids[callback_query.from_user.id] = [night_owl_message.message_id]

@dp.callback_query_handler(lambda c: c.data in ['night_owl', 'early_bird'])
async def handle_night_owl(callback_query: types.CallbackQuery):
    night_owl = callback_query.data
    user_id = callback_query.from_user.id

    # Сохранение ответа в базу данных
    cursor.execute("INSERT INTO user_answers (user_id, question, answer) VALUES (?, ?, ?)", (user_id, 'night_owl', night_owl))
    conn.commit()

    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    sport_markup = InlineKeyboardMarkup(row_width=1)
    sport_markup.add(
        InlineKeyboardButton('Положительно (занимаюсь!)', callback_data='sport_positive'),
        InlineKeyboardButton('Нейтрально (не занимаюсь спортом)', callback_data='sport_neutral'),
        InlineKeyboardButton('Негативно', callback_data='sport_negative')
    )

    sport_message = await bot.send_message(callback_query.from_user.id, "Как относишься к спорту?", reply_markup=sport_markup)
    user_message_ids[callback_query.from_user.id] = [sport_message.message_id]
@dp.callback_query_handler(lambda c: c.data.startswith('sport_'))
async def handle_sport(callback_query: types.CallbackQuery):
    sport = callback_query.data.split('_')[1]
    user_id = callback_query.from_user.id

    # Сохранение ответа в базу данных
    cursor.execute("INSERT INTO user_answers (user_id, question, answer) VALUES (?, ?, ?)", (user_id, 'sport', sport))
    conn.commit()

    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    summer_markup = InlineKeyboardMarkup(row_width=1)
    summer_markup.add(
        InlineKeyboardButton('Ботать!!!', callback_data='summer_study'),
        InlineKeyboardButton('Чиллить', callback_data='summer_chill')
    )

    summer_message = await bot.send_message(callback_query.from_user.id,"Чем планируешь заниматься летом?", reply_markup=summer_markup)
    user_message_ids[callback_query.from_user.id] = [summer_message.message_id]

@dp.callback_query_handler(lambda c: c.data.startswith('summer_'))
async def handle_summer(callback_query: types.CallbackQuery):
    summer = callback_query.data.split('_')[1]
    user_id = callback_query.from_user.id

    # Сохранение ответа в базу данных
    cursor.execute("INSERT INTO user_answers (user_id, question, answer) VALUES (?, ?, ?)", (user_id, 'summer', summer))
    conn.commit()

    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    extrovert_markup = InlineKeyboardMarkup(row_width=1)
    extrovert_markup.add(
        InlineKeyboardButton('Экстраверт (любишь общаться)', callback_data='extrovert'),
        InlineKeyboardButton('Интроверт (любишь быть один)', callback_data='introvert')
    )

    extrovert_message = await bot.send_message(callback_query.from_user.id, "Ты больше...",
                                               reply_markup=extrovert_markup)
    user_message_ids[callback_query.from_user.id] = [extrovert_message.message_id]

@dp.callback_query_handler(lambda c: c.data in ['extrovert', 'introvert'])
async def handle_extrovert(callback_query: types.CallbackQuery):
    extrovert = callback_query.data
    user_id = callback_query.from_user.id
    # Сохранение ответа в базу данных
    cursor.execute("INSERT INTO user_answers (user_id, question, answer) VALUES (?, ?, ?)",
                   (user_id, 'extrovert', extrovert))
    conn.commit()

    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    season_markup = InlineKeyboardMarkup(row_width=1)
    season_markup.add(
        InlineKeyboardButton('Осень', callback_data='season_autumn'),
        InlineKeyboardButton('Весна', callback_data='season_spring'),
        InlineKeyboardButton('Зима', callback_data='season_winter'),
        InlineKeyboardButton('Лето', callback_data='season_summer')
    )

    season_message = await bot.send_message(callback_query.from_user.id, "Твоё любимое время года?",
                                            reply_markup=season_markup)
    user_message_ids[callback_query.from_user.id] = [season_message.message_id]

@dp.callback_query_handler(lambda c: c.data.startswith('season_'))
async def handle_season(callback_query: types.CallbackQuery):
    season = callback_query.data.split('_')[1]
    user_id = callback_query.from_user.id
    # Сохранение ответа в базу данных
    cursor.execute("INSERT INTO user_answers (user_id, question, answer) VALUES (?, ?, ?)", (user_id, 'season', season))
    conn.commit()

    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    joke_markup = InlineKeyboardMarkup(row_width=1)
    joke_markup.add(
        InlineKeyboardButton('Я на 99 состою из шуточек', callback_data='joke_yes'),
        InlineKeyboardButton('Ой, это не моя тема', callback_data='joke_no')
    )

    joke_message = await bot.send_message(callback_query.from_user.id, "Часто шутишь? Делаешь мемы?",
                                          reply_markup=joke_markup)
    user_message_ids[callback_query.from_user.id] = [joke_message.message_id]

@dp.callback_query_handler(lambda c: c.data.startswith('joke_'))
async def handle_joke(callback_query: types.CallbackQuery):
    joke = callback_query.data.split('_')[1]
    user_id = callback_query.from_user.id
    # Сохранение ответа в базу данных
    cursor.execute("INSERT INTO user_answers (user_id, question, answer) VALUES (?, ?, ?)", (user_id, 'joke', joke))
    conn.commit()

    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    final_markup = InlineKeyboardMarkup(row_width=1)
    final_markup.add(
        InlineKeyboardButton('Начать поиск', callback_data='start_search'),
        InlineKeyboardButton('Вернуться назад', callback_data='main_menu')
    )

    final_message = await bot.send_message(callback_query.from_user.id,
                                           "Супер! Теперь можно начать поиск друга 🥰\n\n"
                                           "Жми на кнопку 👇🏼",
                                           reply_markup=final_markup)
    user_message_ids[callback_query.from_user.id] = [final_message.message_id]

@dp.callback_query_handler(lambda c: c.data == 'start_search')
async def start_search(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
    user_id = callback_query.from_user.id

    # Получение ответов пользователя
    cursor.execute("SELECT question, answer FROM user_answers WHERE user_id = ?", (user_id,))
    user_answers = cursor.fetchall()

    # Поиск пользователей с совпадающими ответами
    matches = {}
    for question, answer in user_answers:
        cursor.execute("SELECT user_id FROM user_answers WHERE question = ? AND answer = ? AND user_id != ?",
                       (question, answer, user_id))
        results = cursor.fetchall()
        for (matched_user_id,) in results:
            if matched_user_id not in matches:
                matches[matched_user_id] = 0
            matches[matched_user_id] += 1

    # Фильтрация пользователей с 6 и более совпадениями
    matched_users = [user for user, count in matches.items() if count >= 6]

    if matched_users:
        matched_usernames = []
        for matched_user_id in matched_users:
            cursor.execute("SELECT username FROM users WHERE id = ?", (matched_user_id,))
            username = cursor.fetchone()[0]
            matched_usernames.append(username)

        matched_usernames_str = "\n".join(f"{i + 1}. @{username}" for i, username in enumerate(matched_usernames))

        await bot.send_message(callback_query.from_user.id,
                               f"Нашли несколько ребят, с которыми у тебя точный мэтч!\n\n{matched_usernames_str}\n\nСмело пиши им и знакомься ❤️")
    else:
        await bot.send_message(callback_query.from_user.id, "К сожалению, мы не нашли никого с подходящими ответами.")

    await bot.send_message(callback_query.from_user.id, "Возвращаемся в меню", reply_markup=menu_markup)


# Определение административного меню
def get_admin_markup():
    admin_markup = InlineKeyboardMarkup(row_width=1)
    admin_markup.add(
        InlineKeyboardButton('Выгрузить таблицы', callback_data='export_tables'),
        InlineKeyboardButton('Рассылка по всей базе', callback_data='broadcast_all'),
        InlineKeyboardButton('Рассылка по конкретным пользователям', callback_data='broadcast_users'),
        InlineKeyboardButton('Редактировать баллы пользователя', callback_data='edit_points'),
        InlineKeyboardButton('Добавить кодовое слово', callback_data='add_codeword'),
        InlineKeyboardButton('Удалить кодовое слово', callback_data='delete_codeword'),
        InlineKeyboardButton('Показать все кодовые слова', callback_data='show_codewords')
    )
    return admin_markup


# Состояния для FSM
class CodewordForm(StatesGroup):
    waiting_for_codeword = State()
    waiting_for_points = State()


class DeleteCodewordForm(StatesGroup):
    waiting_for_codeword = State()


# Обработчик команды /admin
@dp.message_handler(commands=['admin'])
async def admin_menu(message: types.Message):
    if message.from_user.id not in ADMIN_ID:
        await message.reply("У вас нет прав для доступа к этому меню.")
        return

    await message.answer("Административное меню", reply_markup=get_admin_markup())


# Обработчик для кнопки "Выгрузить таблицы"
@dp.callback_query_handler(lambda c: c.data == 'export_tables')
async def export_tables(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    # Выгрузка таблицы пользователей
    cursor.execute("SELECT * FROM users")
    users_data = cursor.fetchall()
    users_df = pd.DataFrame(users_data, columns=['id', 'username', 'points'])
    users_df.to_excel('users_table.xlsx', index=False)

    # Выгрузка таблицы ответов пользователей
    cursor.execute("SELECT * FROM user_answers")
    answers_data = cursor.fetchall()
    answers_df = pd.DataFrame(answers_data, columns=['user_id', 'question', 'answer'])
    answers_df.to_excel('user_answers_table.xlsx', index=False)

    await bot.send_message(callback_query.from_user.id, "Таблицы выгружены в файлы Excel.")
    await bot.send_document(callback_query.from_user.id, open('users_table.xlsx', 'rb'))
    await bot.send_document(callback_query.from_user.id, open('user_answers_table.xlsx', 'rb'))
    await bot.send_message(callback_query.from_user.id, "Административное меню", reply_markup=get_admin_markup())


# Обработчик для кнопки "Рассылка по всей базе"
@dp.callback_query_handler(lambda c: c.data == 'broadcast_all')
async def broadcast_all(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id, "Введите сообщение для рассылки по всей базе:")

    @dp.message_handler()
    async def send_broadcast(message: types.Message):
        if message.from_user.id not in ADMIN_ID:
            return

        cursor.execute("SELECT id FROM users")
        user_ids = cursor.fetchall()
        for (user_id,) in user_ids:
            try:
                await bot.send_message(user_id, message.text)
            except Exception as e:
                logging.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

        await message.reply("Сообщение разослано по всей базе.")

        # Удаление обработчика после получения сообщения
        dp.message_handlers.unregister(send_broadcast)

# Обработчик для кнопки "Назад" или "Главное меню"
@dp.callback_query_handler(lambda c: c.data == 'main_menu')
async def process_callback_button_main_menu(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Возвращаемся в меню", reply_markup=menu_markup)
    # Удаление обработчика сообщения при возвращении в главное меню
    dp.message_handlers.unregister(send_broadcast)


# Обработчик для кнопки "Рассылка по конкретным пользователям"
@dp.callback_query_handler(lambda c: c.data == 'broadcast_users')
async def broadcast_users(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id,
                           "Введите список ID пользователей через запятую и сообщение для рассылки в формате:\n\nID1,ID2,...,IDN: Ваше сообщение")

    @dp.message_handler()
    async def send_broadcast_to_users(message: types.Message):
        if message.from_user.id not in ADMIN_ID:
            return

        try:
            user_ids_str, text = message.text.split(':')
            user_ids = [int(uid.strip()) for uid in user_ids_str.split(',')]
            for user_id in user_ids:
                try:
                    await bot.send_message(user_id, text.strip())
                except Exception as e:
                    logging.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

            await message.reply("Сообщение разослано указанным пользователям.")
        except Exception as e:
            await message.reply(f"Ошибка в формате ввода: {e}")


from aiogram.dispatcher.filters import Text
class EditPointsForm(StatesGroup):
    waiting_for_points = State()
# Обработчик для кнопки "Редактировать баллы пользователя"
# Обработчик для кнопки "Редактировать баллы пользователя"
from aiogram.dispatcher import FSMContext

# Обработчик для кнопки "Редактировать баллы пользователя"
@dp.callback_query_handler(lambda c: c.data == 'edit_points')
async def edit_points(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id,
                           "Введите ID пользователя и новое количество баллов в формате:\n\nID: Новое количество баллов")
    await EditPointsForm.waiting_for_points.set()

@dp.message_handler(state=EditPointsForm.waiting_for_points)
async def update_points(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_ID:
        return

    try:
        user_id, points = message.text.split(':')
        user_id = int(user_id.strip())
        points = int(points.strip())
        cursor.execute("UPDATE users SET points = ? WHERE id = ?", (points, user_id))
        conn.commit()
        await message.reply(f"Баллы пользователя {user_id} обновлены до {points}.")
    except Exception as e:
        await message.reply(f"Ошибка в формате ввода: {e}")
    finally:
        await state.finish()

    # Регистрируем временный обработчик сообщений
    dp.message_handlers.register(update_points, content_types=types.ContentType.TEXT)

# Обработчик для кнопки "Назад" или "Главное меню"
@dp.callback_query_handler(lambda c: c.data == 'main_menu')
async def process_callback_button_main_menu(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Возвращаемся в меню", reply_markup=menu_markup)
    # Удаление всех временных обработчиков сообщений при возвращении в главное меню
    dp.message_handlers.handlers.clear()

# Обработчик для кнопки "Добавить кодовое слово"
@dp.callback_query_handler(lambda c: c.data == 'add_codeword')
async def add_codeword(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id, "Введите новое кодовое слово:")
    await CodewordForm.waiting_for_codeword.set()


@dp.message_handler(state=CodewordForm.waiting_for_codeword)
async def process_codeword(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['codeword'] = message.text

    await message.reply("Введите количество баллов за это кодовое слово:")
    await CodewordForm.next()


@dp.message_handler(state=CodewordForm.waiting_for_points)
async def process_points(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        codeword = data['codeword']
        points = int(message.text)
        cursor.execute("INSERT INTO codewords (code, points) VALUES (?, ?)", (codeword, points))
        conn.commit()

    await message.reply(f"Кодовое слово '{codeword}' добавлено с количеством баллов {points}.",
                        reply_markup=get_admin_markup())
    await state.finish()


# Обработчик для кнопки "Удалить кодовое слово"
@dp.callback_query_handler(lambda c: c.data == 'delete_codeword')
async def delete_codeword(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id, "Введите кодовое слово для удаления:")
    await DeleteCodewordForm.waiting_for_codeword.set()


@dp.message_handler(state=DeleteCodewordForm.waiting_for_codeword)
async def process_delete_codeword(message: types.Message, state: FSMContext):
    codeword = message.text
    cursor.execute("DELETE FROM codewords WHERE code = ?", (codeword,))
    conn.commit()

    await message.reply(f"Кодовое слово '{codeword}' удалено.", reply_markup=get_admin_markup())
    await state.finish()


# Обработчик для кнопки "Показать все кодовые слова"
@dp.callback_query_handler(lambda c: c.data == 'show_codewords')
async def show_codewords(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)

    cursor.execute("SELECT code, points FROM codewords")
    codewords = cursor.fetchall()

    if codewords:
        codewords_str = "\n".join([f"{codeword}: {points} баллов" for codeword,points in codewords])
        await bot.send_message(callback_query.from_user.id, f"Список кодовых слов и баллов:\n\n{codewords_str}", reply_markup=get_admin_markup())
    else:
        await bot.send_message(callback_query.from_user.id, "Кодовые слова не найдены.", reply_markup=get_admin_markup())

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)