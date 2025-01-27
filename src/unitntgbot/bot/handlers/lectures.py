# /menu .......... Mostra il menu del ristorante
# /menu dinner ... Mostra il menu del ristorante Cena (solo a Tommaso Gar)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


async def lectures_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Verifica se esite il token associato all'utente

    # Se esiste
    # Mostra le lezioni

    # Se non esiste
    # Mostra un messaggio di aggiungere il token 
    #local:748484/lectures/{tguid}/{date}
    # -> 404
    # ue usa /addlectures
    
    # else 
    # users join lectures on lectureid where date = ?, today
    

    if update.message:
        await update.message.reply_text()


def add_lectures_handler():
    # local:748484/add/{tguid}?url={url}
    # --> srapa le robe -> si aggiunge su table Users tguid: lectureID 
    
    pass

async def lectures_callback_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query:
        return

    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Option 1", callback_data="a" * 6)],
        [InlineKeyboardButton("Option 2", callback_data="menu2")],
        [InlineKeyboardButton("Visit Website", url="https://example.com")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Respond to the button click based on callback data
    if query.data == "1":
        await query.edit_message_text(text="You selected Option 1.")
    elif query.data == "2":
        await query.edit_message_text(text="Option 2 selected", reply_markup=reply_markup)
