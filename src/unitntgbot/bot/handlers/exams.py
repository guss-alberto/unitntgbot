import requests

from telegram import Update
from telegram.ext import ContextTypes

from unitntgbot.backend.exams.UniversityExam import UniversityExam

# TODO: pages
async def exams_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    
    if not context.args:
        tg_id = update.message.chat_id
        api_url = f"http://127.0.0.1:5003/exams/user/{tg_id}"
        response = requests.get(api_url)
    else:
        query = " ".join(context.args)
        api_url = "http://127.0.0.1:5003/exams/search"
        response = requests.get(api_url, params={"query": query})

    match(response.status_code):
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
