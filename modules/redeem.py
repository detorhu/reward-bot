from telegram import Update
from telegram.ext import ContextTypes

async def redeem_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "*Redeem System*\n\n"
        "This section will allow users to redeem their points for rewards.\n"
        "The feature is currently under development.",
        parse_mode="Markdown"
    )
