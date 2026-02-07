from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import time

# ================= USER REDEEM MENU =================
async def redeem_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    kb = [
        [InlineKeyboardButton("🎁 Redeem Rewards", callback_data="redeem_reward")],
        [InlineKeyboardButton("📱 Mobile Recharge", callback_data="redeem_recharge")],
        [InlineKeyboardButton("💵 Cash / UPI Withdrawal", callback_data="redeem_cash")],
        [InlineKeyboardButton("🛒 Custom Products", callback_data="redeem_custom")],
        [InlineKeyboardButton("🔙 Back", callback_data="start_back")]
    ]

    await q.message.edit_text(
        "🎯 *Redeem Your Points*\n\n"
        "Apne points ko rewards, recharge ya cash me convert karo 💰\n"
        "Sabhi redeem requests admin verify karega (100% safe & genuine).",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ================= COMMON REDEEM HANDLER =================
async def create_redeem_request(update, context, redeem_type):
    q = update.callback_query
    await q.answer()

    db = context.application.bot_data["db"]
    users = db.users
    redeems = db.redeems

    user = users.find_one({"_id": q.from_user.id})

    if not user or user.get("points", 0) <= 0:
        await q.message.edit_text("❌ Aapke paas redeem ke liye sufficient points nahi hain.")
        return

    redeem_id = f"redeem_{int(time.time())}"

    redeems.insert_one({
        "_id": redeem_id,
        "user": q.from_user.id,
        "type": redeem_type,
        "points": user["points"],
        "status": "pending",
        "time": time.time()
    })

    await q.message.edit_text(
        "✅ *Redeem Request Submitted*\n\n"
        f"🔹 Type: {redeem_type}\n"
        f"🎯 Points Used: {user['points']}\n\n"
        "Admin jaldi hi verify karega aur aapse contact karega.",
        parse_mode="Markdown"
    )

# ================= INDIVIDUAL OPTIONS =================
async def redeem_reward(update, context):
    await create_redeem_request(update, context, "Reward")

async def redeem_recharge(update, context):
    await create_redeem_request(update, context, "Recharge")

async def redeem_cash(update, context):
    await create_redeem_request(update, context, "Cash / UPI")

async def redeem_custom(update, context):
    await create_redeem_request(update, context, "Custom Product")
