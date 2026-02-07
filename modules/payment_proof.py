from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

async def receive_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = message.from_user

    # Photo check
    if not message.photo:
        await message.reply_text("❌ Please send a payment screenshot only.")
        return

    # Order ID check
    if not context.user_data.get("waiting_for_screenshot"):
        await message.reply_text(
            "❌ No pending order found.\n"
            "Please click *I Have Paid* first.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    order_id = context.user_data.pop("waiting_for_screenshot")

    caption = (
        f"🧾 *Payment Screenshot Received*\n\n"
        f"👤 User ID: `{user.id}`\n"
        f"👤 Username: @{user.username}\n"
        f"🆔 Order ID: `{order_id}`"
    )

    # Forward to admin
    await message.copy(
        chat_id=context.application.bot_data["ADMIN_ID"],
        caption=caption,
        parse_mode=ParseMode.MARKDOWN
    )

    await message.reply_text(
        "✅ Screenshot received successfully.\n"
        "Please wait for admin approval."
    )
