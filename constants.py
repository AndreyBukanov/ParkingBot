import os
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, constants

# States
ST_BEGIN: int = 0
ST_NEW_PASS: int = 1
ST_FILL: int = 2
ST_ASK: int = 3
ST_END: int = 4

# Buttons
NEW = "Редактировать"
REPEAT = "Повторить"

YES = "Да"
NO = "Нет"

NUMBER = "Номер"
MODEL = "Марка"
REASON = "Причина"
DATE = "Дата"
SEND = "Отправить"
BACK = "Назад"

ACTION = "action"

# Token
TOKEN = os.environ.get("BOT_TOKEN")
GROUP_ID = os.environ.get("BOT_GROUP_ID")

# Mail
FROM_EMAIL = os.environ.get("BOT_FROM_EMAIL")
TO_EMAIL = os.environ.get("BOT_TO_EMAIL")
EMAIL_PASS = os.environ.get("BOT_EMAIL_PASS")

SMTP_ADDRESS = os.environ.get("BOT_SMTP_ADDRESS")
SMTP_PORT = os.environ.get("BOT_SMTP_PORT")

# Member lists
bad_list = [constants.ChatMemberStatus.RESTRICTED,
            constants.ChatMemberStatus.BANNED,
            constants.ChatMemberStatus.LEFT]

good_list = [constants.ChatMemberStatus.OWNER,
             constants.ChatMemberStatus.MEMBER]

# Keyboard
begin_keyboard = [
    [NEW],
    [REPEAT],
]
begin_markup = ReplyKeyboardMarkup(begin_keyboard, one_time_keyboard=True)

fill_keyboard = [
    [BACK],
    [NUMBER, MODEL],
    [REASON, DATE],
    [SEND],
]
fill_markup = ReplyKeyboardMarkup(fill_keyboard, one_time_keyboard=True)

ask_keyboard = [
    [YES, NO],
]
ask_markup = ReplyKeyboardMarkup(ask_keyboard, one_time_keyboard=True)

remove_keyboard = ReplyKeyboardRemove()
