import httpx
from exams.UniversityExam import UniversityExam
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot_frontend.settings import settings
from bot_frontend.utils import edit_message_text_without_changes


def get_keyboard(callback: str, page: int, n_pages: int) -> InlineKeyboardMarkup:
    has_next = page < n_pages
    has_prev = page > 1

    keyboard: list[InlineKeyboardButton] = []
    if has_prev:
        keyboard.append(InlineKeyboardButton("⬅️", callback_data=f"exams:{page - 1}:{callback}"))
    else:
        keyboard.append(InlineKeyboardButton(" ", callback_data=" "))

    if has_next:
        keyboard.append(InlineKeyboardButton("➡️", callback_data=f"exams:{page + 1}:{callback}"))
    else:
        keyboard.append(InlineKeyboardButton(" ", callback_data=" "))

    return InlineKeyboardMarkup([keyboard])


def process_results(response, callback) -> tuple[str, InlineKeyboardMarkup | None]:
    match response.status_code:
        case 200:
            data = response.json()
            exams = [UniversityExam(**exam) for exam in data["exams"]]
            exams_formatted = "\n\n".join([exam.format() for exam in exams])

            markup = None

            message = f"<b>{data['n_items']} exams found</b>\n\n{exams_formatted}"

            if len(exams) < data["n_items"]:
                markup = get_keyboard(callback, data["page"], data["n_pages"])
                message += f"\n\n <i>Page {data['page']} of {data['n_pages']}</i>"

            return message, markup
        case 400 | 404:
            data = response.json()
            return data["message"], None
        case 500:
            return "Internal Server Error", None
        case _:
            return "An unknown error occured", None


async def exams_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    if not context.args:
        await update.message.reply_html("Please provide a search query\n\nUsage:\n/exams <code>&lt;query&gt;")
        return
        #tg_id = update.message.chat_id
        #callback = f"u:{tg_id}"
        #async with httpx.AsyncClient() as client:
        #    response = await client.get(f"{settings.EXAMS_SVC_URL}/exams/user/{tg_id}/", timeout=30)
    else:
        query = " ".join(context.args)
        callback = f"q:{query}"
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.EXAMS_SVC_URL}/exams/search", params={"query": query}, timeout=30)

        msg, markup = process_results(response, callback)
        await update.message.reply_html(msg, reply_markup=markup, disable_web_page_preview=True)


async def exams_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query or not query.data or not query.message:
        return

    _, page, query_type, *param = query.data.split(":")
    param = ":".join(param)

    if query_type == "u":
        callback = f"u:{param}"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.EXAMS_SVC_URL}/exams/user/{param}",
                params={"page": page},
                timeout=30,
            )
    else:
        callback = f"q:{param}"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.EXAMS_SVC_URL}/exams/search",
                params={"query": param, "page": page},
                timeout=30,
            )

    msg, markup = process_results(response, callback)
    await edit_message_text_without_changes(
        query,
        msg,
        reply_markup=markup,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
