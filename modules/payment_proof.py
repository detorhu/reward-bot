from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

async def receive_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = message.from_user

    # ❌ Ignore non-photo messages
    if not message.photo:
        return

    # 🔒 Check if bot is waiting for screenshot
    if "waiting_for_screenshot" not in context.user_data:
        return

    order_id = context.user_data.pop("waiting_for_screenshot")

    # 🔌 Get DB & ADMIN
    db = context.application.bot_data.get("db")
    admin_id = context.application.bot_data.get("ADMIN_ID")

    if db is None or admin_id is None:
        await message.reply_text("❌ Internal error. Try again later.")
        return

    orders = db.orders
    order = orders.find_one({"_id": order_id})

    if not order:
        await message.reply_text("❌ Order not found. Please contact support.")
        return

    # 📸 Get highest quality photo
    photo = message.photo[-1]

    # 💾 Save proof in DB
    orders.update_one(
        {"_id": order_id},
        {"$set": {
            "payment_proof": photo.file_id,
            "status": "submitted"
        }}
    )

    caption = (
        f"🧾 *Payment Screenshot Received*\n\n"
        f"👤 User ID: `{user.id}`\n"
        f"👤 Username: @{user.username}\n"
        f"🆔 Order ID: `{order_id}`\n"
        f"📦 Product: {order.get('product')}\n"
        f"💰 Amount: ₹{order.get('price')}"
    )

    # 📤 Send proof to admin
    await context.bot.send_photo(
        chat_id=admin_id,
        photo=photo.file_id,
        caption=caption,
        parse_mode=ParseMode.MARKDOWN
    )

    # ✅ Confirm to user
    await message.reply_text(
        "✅ *Screenshot received successfully!*\n\n"
        "Admin will verify your payment shortly.",
        parse_mode=ParseMode.MARKDOWN
        )
