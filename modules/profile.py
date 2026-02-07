from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import time, html

# ================= PROFILE ENTRY (HANDLER TARGET) =================
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q:
        return
    await profile_menu(update, context)

# ================= PROFILE MENU =================
async def profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q:
        return
    await q.answer()

    # ✅ DB FETCH (MISSING EARLIER)
    db = context.application.bot_data.get("db")
    if not db:
        await q.message.edit_text("❌ Database connection error.")
        return

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
        f"💰 <b>Points Balance:</b> {user.get('points', 0)}\n"
        f"👥 <b>Total Referrals:</b> {user.get('referrals', 0)}\n\n"
        f"🛒 <b>Total Orders:</b> {total_orders}\n"
        f"✅ <b>Completed Orders:</b> {completed_orders}\n\n"
        f"📅 <b>Joined On:</b> {joined_date}"
    )

    kb = [
        [InlineKeyboardButton("🛒 My Orders", callback_data="profile_orders")],
        [InlineKeyboardButton("👥 Referral Info", callback_data="profile_referrals")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="start_back")]
    ]

    await q.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ================= ORDER HISTORY =================
async def profile_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q:
        return
    await q.answer()

    db = context.application.bot_data.get("db")
    orders = db.orders

    cursor = orders.find({"user": q.from_user.id}).sort("_id", -1).limit(10)

    text = "🛒 <b>Your Recent Orders</b>\n\n"
    found = False

    for o in cursor:
        found = True
        text += (
            f"📦 <b>Product:</b> {html.escape(o['product'])}\n"
            f"💰 <b>Price:</b> ₹{o['price']}\n"
            f"🎯 <b>Discount Used:</b> {o.get('discount', 0)}\n"
            f"📌 <b>Status:</b> {html.escape(o['status'])}\n\n"
        )

    if not found:
        text = "❌ You have not placed any orders yet."

    kb = [[InlineKeyboardButton("🔙 Back to Profile", callback_data="profile")]]

    await q.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ================= REFERRAL INFO =================
async def profile_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q:
        return
    await q.answer()

    db = context.application.bot_data.get("db")
    users = db.users
    user = users.find_one({"_id": q.from_user.id})

    referred_by = user.get("referred_by")
    referred_text = f"<code>{referred_by}</code>" if referred_by else "No one (Direct user)"

    text = (
        "👥 <b>Referral Information</b>\n\n"
        f"👤 <b>Referred By:</b> {referred_text}\n"
        f"👥 <b>Total Referrals:</b> {user.get('referrals', 0)}\n"
        f"💰 <b>Points Earned:</b> {user.get('referrals', 0) * 5}\n\n"
        "Invite more users to earn more points."
    )

    kb = [[InlineKeyboardButton("🔙 Back to Profile", callback_data="profile")]]

    await q.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(kb)
    )
