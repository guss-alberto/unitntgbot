from collections.abc import Sequence
from typing import Optional

from telegram import CallbackQuery, InlineKeyboardMarkup, LinkPreviewOptions, Message, MessageEntity
from telegram._utils.defaultvalue import DEFAULT_NONE
from telegram._utils.types import JSONDict, ODVInput
from telegram.error import BadRequest


async def edit_message_text_without_changes(
    query: CallbackQuery,
    text: str,
    parse_mode: ODVInput[str] = DEFAULT_NONE,
    reply_markup: Optional["InlineKeyboardMarkup"] = None,
    entities: Sequence["MessageEntity"] | None = None,
    link_preview_options: ODVInput["LinkPreviewOptions"] = DEFAULT_NONE,
    *,
    disable_web_page_preview: bool | None = None,
    read_timeout: ODVInput[float] = DEFAULT_NONE,
    write_timeout: ODVInput[float] = DEFAULT_NONE,
    connect_timeout: ODVInput[float] = DEFAULT_NONE,
    pool_timeout: ODVInput[float] = DEFAULT_NONE,
    api_kwargs: JSONDict | None = None,
) -> Message | bool:
    """
    Telegram will raise an error if the message is not modified
    Shortcut for::

        await query.edit_message_text(*args, **kwargs)

    For the documentation of the arguments, please see
    :meth:`telegram.Bot.edit_message_text` and :meth:`telegram.Message.edit_text`.

    .. versionchanged:: 20.8
        Raises :exc:`TypeError` if :attr:`message` is not accessible.

    Returns:
        :class:`telegram.Message`: On success, if edited message is sent by the bot, the
        edited Message is returned, otherwise :obj:`True` is returned.

    Raises:
        :exc:`TypeError` if :attr:`message` is not accessible.

    """

    try:
        return await query.edit_message_text(
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
            link_preview_options=link_preview_options,
            reply_markup=reply_markup,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            connect_timeout=connect_timeout,
            pool_timeout=pool_timeout,
            api_kwargs=api_kwargs,
            entities=entities,
        )
    except BadRequest as e:
        if "Message is not modified" not in e.message:
            raise

    return False
