# /menu ................. Mostra il menu del ristorante
# /menu cena ............ Mostra il menu del ristorante Cena (solo a Tommaso Gar)
# /menu calendario ...... Scarica il PDF del calendario (da decidere)

from telegram import Update
from telegram.ext import ContextTypes


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass


async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass
