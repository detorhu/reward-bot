from telegram import Update
from telegram.ext import ContextTypes

async def reward_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    await q.message.reply_text(
        "🎁 *Rewards*\n\n"
        "Daily / special rewards yaha dikhenge.\n"
        "🚧 Under development",
        parse_mode="Markdown"
    )
