from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import time

# ================= PROFILE MENU =================
async def profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    db = context.application.bot_data.get("db")
    if not db:
        await q.message.reply_text("Database connection error.")
        return

    users = db.users
    orders = db.orders

    user = users.find_one({"_id": q.from_user.id})
    if not user:
        await q.message.reply_text("User profile not found.")
        return

    total_orders = orders.count_documents({"user": q.from_user.id})
    completed_orders = orders.count_documents({
        "user": q.from_user.id,
        "status": "delivered"
    })

    joined_time = user.get("joined", time.time())
    joined_date = time.strftime("%d %b %Y", time.localtime(joined_time))

    text = (
        "👤 *Your Profile*\n\n"
        f"🆔 User ID: `{user['_id']}`\n"
        f"👤 Username: @{user.get('username', 'Not set')}\n\n"
        f"💰 Points Balance: {user.get('points', 0)}\n"
        f"👥 Total Referrals: {user.get('referrals', 0)}\n\n"
        f"🛒 Total Orders: {total_orders}\n"
        f"✅ Completed Orders: {completed_orders}\n\n"
        f"📅 Joined On: {joined_date}"
    )

    kb = [
        [InlineKeyboardButton("🛒 My Orders", callback_data="profile_orders")],
        [InlineKeyboardButton("👥 Referral Info", callback_data="profile_referrals")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="start_back")]
    ]

    await q.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )


# ================= ORDER HISTORY =================
async def profile_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    db = context.application.bot_data.get("db")
    orders = db.orders

    user_orders = orders.find(
        {"user": q.from_user.id}
    ).sort("_id", -1).limit(10)

    text = "🛒 *Your Recent Orders*\n\n"
    found = False

    for o in user_orders:
        found = True
        text += (
            f"📦 Product: {o['product']}\n"
            f"💰 Price: ₹{o['price']}\n"
            f"🎯 Discount Used: {o.get('discount', 0)}\n"
            f"📌 Status: *{o['status']}*\n\n"
        )

    if not found:
        text = "❌ You have not placed any orders yet."

    kb = [[InlineKeyboardButton("🔙 Back to Profile", callback_data="profile")]]

    await q.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )


# ================= REFERRAL INFO =================
async def profile_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    db = context.application.bot_data.get("db")
    users = db.users

    user = users.find_one({"_id": q.from_user.id})

    referred_by = user.get("referred_by")
    referred_text = (
        f"`{referred_by}`" if referred_by else "No one (Direct user)"
    )

    text = (
        "👥 *Referral Information*\n\n"
        f"👤 Referred By: {referred_text}\n"
        f"👥 Total Referrals: {user.get('referrals', 0)}\n"
        f"💰 Points Earned from Referrals: {user.get('referrals', 0) * 5}\n\n"
        "Invite more users to earn more points."
    )

    kb = [[InlineKeyboardButton("🔙 Back to Profile", callback_data="profile")]]

    await q.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
      )
