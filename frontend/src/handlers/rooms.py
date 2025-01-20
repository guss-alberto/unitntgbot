# /rooms ................ Mostra le aule libere e occupate del dipartimento di default (con una Warning che dice di poter cambiare il dipartimento di default)
# /rooms povo ........... Mostra le aule libere e occupate a Povo
# /rooms mesiano ........ Mostra le aule libere e occupate a Mesiano
# /rooms povo A101 ...... Mostra le informazioni sull'aula A101 a Povo durante tutto il giorno

from telegram import Update
from telegram.ext import ContextTypes


async def rooms_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass
    # keyboard = [
    #     [InlineKeyboardButton("", callback_data="1")],
    #     [InlineKeyboardButton("Option 2", callback_data="2")],
    #     [InlineKeyboardButton("Visit Website", url="https://example.com")],
    # ]

    # reply_markup = InlineKeyboardMarkup(keyboard)

    # await update.message.reply_text("Choose an option:", reply_markup=reply_markup)


async def rooms_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass
    # query = update.callback_query await query.answer()

    # keyboard = [
    #     [InlineKeyboardButton("Option 1", callback_data="1")],
    #     [InlineKeyboardButton("Option 2", callback_data="2")],
    #     [InlineKeyboardButton("Visit Website", url="https://example.com")],
    # ]

    # reply_markup = InlineKeyboardMarkup(keyboard)

    # # Respond to the button click based on callback data
    # if query.data == "1":
    #     await query.edit_message_text(text="You selected Option 1.")
    # elif query.data == "2":
    #     await query.edit_message_text(text="Option 2 selected", reply_markup=reply_markup)
