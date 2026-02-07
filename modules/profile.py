from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import time
import html

# ================= PROFILE ENTRY (IMPORTANT) =================
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    db = context.application.bot_data["db"]
    users = db.users
    orders = db.orders

    user = users.find_one({"_id": q.from_user.id})
    if not user:
        await q.message.edit_text("❌ User profile not found.")
        return

    username = user.get("username")
    username_text = f"@{html.escape(username)}" if username else "Not set"

    total_orders = orders.count_documents({"user": q.from_user.id})
    completed_orders = orders.count_documents(
        {"user": q.from_user.id, "status": "delivered"}
    )

    joined_time = user.get("joined", time.time())
    joined_date = time.strftime("%d %b %Y", time.localtime(joined_time))

    text = (
        "👤 <b>Your Profile</b>\n\n"
        f"🆔 <b>User ID:</b> <code>{user['_id']}</code>\n"
        f"👤 <b>Username:</b> {username_text}\n\n"
        f"💰 <b>Points:</b> {user.get('points', 0)}\n"
        f"👥 <b>Referrals:</b> {user.get('referrals', 0)}\n\n"
        f"🛒 <b>Total Orders:</b> {total_orders}\n"
        f"✅ <b>Completed:</b> {completed_orders}\n\n"
        f"📅 <b>Joined:</b> {joined_date}"
    )

    kb = [
        [InlineKeyboardButton("🛒 My Orders", callback_data="profile_orders")],
        [InlineKeyboardButton("👥 Referral Info", callback_data="profile_referrals")],
        [InlineKeyboardButton("🔙 Back", callback_data="start_back")]
    ]

    await q.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(kb)
    )


# ================= ORDER HISTORY =================
async def profile_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    db = context.application.bot_data["db"]
    orders = db.orders

    cursor = orders.find({"user": q.from_user.id}).sort("_id", -1).limit(10)

    text = "🛒 <b>Your Orders</b>\n\n"
    found = False

    for o in cursor:
        found = True
        text += (
            f"📦 <b>{html.escape(o['product'])}</b>\n"
            f"💰 ₹{o['price']}\n"
            f"📌 {html.escape(o['status'])}\n\n"
        )

    if not found:
        text = "❌ No orders yet."

    kb = [[InlineKeyboardButton("🔙 Back", callback_data="profile")]]

    await q.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(kb)
    )


# ================= REFERRAL INFO =================
async def profile_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    db = context.application.bot_data["db"]
    users = db.users

    user = users.find_one({"_id": q.from_user.id})

    referred_by = user.get("referred_by")
    ref_text = f"<code>{referred_by}</code>" if referred_by else "Direct user"

    text = (
        "👥 <b>Referral Info</b>\n\n"
        f"👤 <b>Referred By:</b> {ref_text}\n"
        f"👥 <b>Total Referrals:</b> {user.get('referrals', 0)}\n"
        f"💰 <b>Points Earned:</b> {user.get('referrals', 0) * 5}"
    )

    kb = [[InlineKeyboardButton("🔙 Back", callback_data="profile")]]

    await q.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(kb)
    )
