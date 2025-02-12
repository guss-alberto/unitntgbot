import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from unitntgbot.backend.exams.api import MAX_PER_PAGE
from unitntgbot.backend.exams.UniversityExam import UniversityExam
from unitntgbot.bot.settings import settings


# TODO: pages
async def exams_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    if not context.args:
        tg_id = update.message.chat_id
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.EXAMS_SVC_URL}/exams/user/{tg_id}", timeout=30)
    else:
        query = " ".join(context.args)
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.EXAMS_SVC_URL}/exams/search", params={"query": query}, timeout=30)

    match response.status_code:
        case 200:
            data = response.json()
            exams = [UniversityExam(*exam) for exam in data["exams"]]
            exams_formatted = "\n\n".join([exam.format() for exam in exams])
            await update.message.reply_markdown(exams_formatted)
        case 400 | 404:
            data = response.json()
            await update.message.reply_markdown_v2(data["message"])
        case 500:
            await update.message.reply_text("Internal Server Error")
        case _:
            await update.message.reply_text("An unknown error occured")
