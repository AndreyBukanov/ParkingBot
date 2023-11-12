import constants as c
import re
from typing import Dict
from datetime import datetime
import logging
from telegram import Update
from telegram.ext import (
    PicklePersistence,
    ApplicationBuilder,
    ContextTypes,
    filters,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
)

from pdf_send import send_mail

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def get_hints(field: str) -> str:
    hint = ""
    match field:
        case c.NUMBER:
            hint = "пример: А 123 ВС 716"
        case c.MODEL:
            hint = "пример: ВАЗ 2101, чёрный "
        case c.REASON:
            hint = "пример: Забрать груз"
        case c.DATE:
            now = datetime.now().strftime("%d.%m.%Y")
            hint = f"пример: {now}"
    return hint


def check_fields(user_data: Dict[str, str]):
    fields = [c.NUMBER, c.MODEL, c.REASON, c.DATE]
    msg = ""
    r = True
    for field in fields:
        if field in user_data.keys():
            value = user_data[field]
        else:
            value = ""
            r = False
        msg += f"{field} - {value}\n"
    return r, msg


def is_number(input_text):
    words = re.findall(r"[A-ZА-Яa-zа-я]+|[0-9]+", input_text)
    if len(words) != 4:
        return False, input_text
    input_text = " ".join(words)
    r = re.match(r"[A-ZА-Яa-zа-я]\s\d\d\d\s[A-ZА-Яa-а-я][A-ZА-Яa-zа-я]\s[0-9]+", input_text)
    if r is None:
        return False, input_text
    return True, input_text


def is_text(input_text):
    words = re.findall(r"[0-9A-ZА-Яa-zа-я]+", input_text)
    if len(words) < 1:
        return False, input_text
    input_text = " ".join(words)
    return True, input_text


def is_date(input_text):
    words = re.findall(r"(3[01]|[12][0-9]|0?[1-9])(\/|\.|\:||\ |\-)(1[0-2]|0?[1-9])\2([0-9]{4})", input_text)
    if len(words) < 1 or len(words[0]) != 4:
        return False, input_text
    input_text = ".".join([words[0][0], words[0][2], words[0][3]])
    return True, input_text


async def enter_state(st: int, msg: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    match st:
        case c.ST_BEGIN:
            markup = c.begin_markup
        case c.ST_NEW_PASS:
            markup = c.fill_markup
        case c.ST_FILL:
            markup = c.remove_keyboard
        case c.ST_ASK:
            markup = c.ask_markup
        case c.ST_END:
            markup = c.remove_keyboard
        case _:
            markup = c.remove_keyboard

    if m := update.message:
        await m.reply_text(msg, reply_markup=markup)

    if m := update.edited_message:
        await m.reply_text(msg, reply_markup=markup)

    if st == c.ST_END:
        return ConversationHandler.END

    return st


async def start_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    allow_enter: bool = True
    msg = ""
    start_state = c.ST_BEGIN

    try:
        user = await context.bot.get_chat_member(chat_id=c.GROUP_ID, user_id=update.message.from_user.id)
        if not user or user.status in c.bad_list:
            allow_enter = False
            start_state = ConversationHandler.END
            await update.message.reply_text("Неавторизованный пользователь!")
            msg = "В доступе отказано... 😭"
    except Exception:
        allow_enter = False
        start_state = ConversationHandler.END
        await update.message.reply_text("Ошибка доступа к группе!")
        msg = "Что-то сломалось... 😭"

    if allow_enter:
        await update.message.reply_text("Парковочный бот НЕОВЭЛЛ!")
        msg = "Нужно отредактировать пропуск или отправить такой-же как в прошлый раз?"

    return await enter_state(start_state, msg, update, context)


async def begin_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if m := update.message:
        if m.text == c.NEW:
            msg = "Редактируем, ок!\nЗаполняем поля:"
            return await enter_state(c.ST_NEW_PASS, msg, update, context)
        if m.text == c.REPEAT:
            context.user_data[c.DATE] = datetime.now().strftime("%d.%m.%Y")
            r, msg = check_fields(context.user_data)
            if r:
                msg += "\n" + "Все ок, отсылаем?"
                return await enter_state(c.ST_ASK, msg, update, context)
            else:
                msg += "Похоже что-то не заполнено... 🤔"
                return await enter_state(c.ST_BEGIN, msg, update, context)

    msg = "Хмм, не понятно... редактируем или отправляем?"
    return await enter_state(c.ST_BEGIN, msg, update, context)


async def new_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if m := update.message:
        if m.text in [c.NUMBER, c.MODEL, c.REASON, c.DATE]:
            context.user_data[c.ACTION] = m.text
            msg = get_hints(m.text) + "\n"
            msg += "записываю " + m.text + ":"
            return await enter_state(c.ST_FILL, msg, update, context)
        if m.text == c.SEND:
            r, msg = check_fields(context.user_data)
            if r:
                msg += "\n" + "Все ок, отсылаем?"
                return await enter_state(c.ST_ASK, msg, update, context)
            else:
                msg += "Похоже что-то не заполнено... 🤔"
                return await enter_state(c.ST_BEGIN, msg, update, context)
        if m.text == c.BACK:
            msg = "Возвращаемся..."
            return await enter_state(c.ST_BEGIN, msg, update, context)

    msg = "Нужно отредактировать или как в прошлый раз?"
    return await enter_state(c.ST_BEGIN, msg, update, context)


async def fill_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = "Что-то на неразборчивом... 🤔"

    if c.ACTION in context.user_data.keys():
        action = context.user_data[c.ACTION]
        value = ""
        r = False

        match action:
            case c.NUMBER:
                r, value = is_number(update.message.text)
            case c.MODEL:
                r, value = is_text(update.message.text)
            case c.REASON:
                r, value = is_text(update.message.text)
            case c.DATE:
                r, value = is_date(update.message.text)

        if r:
            context.user_data[action] = value
            msg = f"Запомнил! {action}: {value}"

    return await enter_state(c.ST_NEW_PASS, msg, update, context)


async def ask_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if m := update.message:
        if m.text == c.YES:
            context.user_data["action"] = m.text
            msg = "Отправил письмо с запросом!"
            name = context.user_data[c.MODEL]
            number = context.user_data[c.NUMBER]
            reason = context.user_data[c.REASON]
            date = context.user_data[c.DATE]
            send_mail(number, name, reason, date)
            return await enter_state(c.ST_BEGIN, msg, update, context)
        if m.text == c.NO:
            context.user_data["action"] = m.text
            msg = "Возвращаемся..."
            return await enter_state(c.ST_BEGIN, msg, update, context)

    context.user_data["action"] = ""
    return await enter_state(c.ST_ASK, "Так да или нет?", update, context)


async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Уронили бота на пол...", reply_markup=c.remove_keyboard)
    return ConversationHandler.END


def main():

    check_list = [c.TOKEN, c.GROUP_ID,
                  c.FROM_EMAIL, c.TO_EMAIL, c.EMAIL_PASS,
                  c.SMTP_ADDRESS, c.SMTP_PORT]

    if any(item is None for item in check_list):
        print("Set ENV variables first!")
        print("Shutting down...")
        return

    # ====================================================================

    persistence = PicklePersistence(filepath="user_database")

    app_builder = ApplicationBuilder()
    app_builder.token(c.TOKEN)
    app_builder.persistence(persistence)

    application = app_builder.build()

    # ====================================================================

    start_h = CommandHandler("start", start_cb)
    entry_points = [start_h]

    begin_h = MessageHandler(~filters.COMMAND, begin_cb)
    new_h = MessageHandler(~filters.COMMAND, new_cb)
    fill_h = MessageHandler(~filters.COMMAND, fill_cb)
    ask_h = MessageHandler(~filters.COMMAND, ask_cb)

    states = {c.ST_BEGIN: [start_h, begin_h],
              c.ST_NEW_PASS: [start_h, new_h],
              c.ST_FILL: [start_h, fill_h],
              c.ST_ASK: [start_h, ask_h]}

    fallback_handler = CommandHandler("fallback", fallback)
    fallbacks = [fallback_handler]

    conv_handler = ConversationHandler(name="my_conversation",
                                       persistent=True,
                                       entry_points=entry_points,
                                       states=states,
                                       fallbacks=fallbacks)

    application.add_handler(conv_handler)

    # ====================================================================

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
