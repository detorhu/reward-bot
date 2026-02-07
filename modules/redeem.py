from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import time
import re

# =================================================
# USER REDEEM MENU
# =================================================
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
        "Sabhi redeem requests admin manually verify karega.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# =================================================
# REDEEM REWARD (SIMPLE)
# =================================================
async def redeem_reward(update, context):
    await create_simple_redeem(update, context, "Reward")

# =================================================
# MOBILE RECHARGE – SHOW PLANS
# =================================================
async def redeem_recharge(update, context):
    q = update.callback_query
    await q.answer()

    db = context.application.bot_data["db"]
    plans = db.redeem_plans.find({"type": "recharge", "active": True})

    kb = []
    for p in plans:
        kb.append([
            InlineKeyboardButton(
                f"{p['title']} – ₹{p['amount']} ({p['points']} pts)",
                callback_data=f"recharge_plan_{p['_id']}"
            )
        ])

    if not kb:
        await q.message.edit_text("❌ No recharge plans available.")
        return

    kb.append([InlineKeyboardButton("🔙 Back", callback_data="redeem")])

    await q.message.edit_text(
        "📱 *Select Recharge Plan*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# =================================================
# CASH / UPI – SHOW OPTIONS
# =================================================
async def redeem_cash(update, context):
    q = update.callback_query
    await q.answer()

    db = context.application.bot_data["db"]
    plans = db.redeem_plans.find({"type": "cash", "active": True})

    kb = []
    for p in plans:
        kb.append([
            InlineKeyboardButton(
                f"₹{p['amount']} Cash ({p['points']} pts)",
                callback_data=f"cash_plan_{p['_id']}"
            )
        ])

    if not kb:
        await q.message.edit_text("❌ No cash options available.")
        return

    kb.append([InlineKeyboardButton("🔙 Back", callback_data="redeem")])

    await q.message.edit_text(
        "💵 *Select Cash Option*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# =================================================
# CUSTOM PRODUCT
# =================================================
async def redeem_custom(update, context):
    q = update.callback_query
    await q.answer()

    context.user_data["redeem_type"] = "custom"

    await q.message.edit_text(
        "🛒 *Custom Redeem*\n\n"
        "Please describe what you want to redeem:",
        parse_mode="Markdown"
    )

# =================================================
# HANDLE PLAN CLICK (RECHARGE / CASH)
# =================================================
async def redeem_plan_selected(update, context):
    q = update.callback_query
    await q.answer()

    db = context.application.bot_data["db"]
    users = db.users
    plans = db.redeem_plans

    plan_id = q.data.split("_")[-1]
    plan = plans.find_one({"_id": plan_id})

    user = users.find_one({"_id": q.from_user.id})

    if not plan or not user:
        await q.message.edit_text("❌ Invalid request.")
        return

    if user["points"] < plan["points"]:
        await q.message.edit_text("❌ Insufficient points.")
        return

    context.user_data["redeem_plan"] = plan
    context.user_data["redeem_type"] = plan["type"]

    if plan["type"] == "recharge":
        await q.message.edit_text("📞 *Enter Mobile Number:*", parse_mode="Markdown")
    else:
        await q.message.edit_text("💰 *Enter UPI ID:*", parse_mode="Markdown")

# =================================================
# TEXT INPUT HANDLER (MOBILE / UPI / CUSTOM)
# =================================================
async def redeem_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "redeem_type" not in context.user_data:
        return

    db = context.application.bot_data["db"]
    redeems = db.redeems
    users = db.users

    user = users.find_one({"_id": update.effective_user.id})
    text = update.message.text.strip()

    redeem_type = context.user_data["redeem_type"]
    plan = context.user_data.get("redeem_plan")

    # Basic validation
    if redeem_type == "recharge" and not re.fullmatch(r"[6-9]\d{9}", text):
        await update.message.reply_text("❌ Invalid mobile number.")
        return

    if redeem_type == "cash" and "@" not in text:
        await update.message.reply_text("❌ Invalid UPI ID.")
        return

    redeem_id = f"redeem_{int(time.time())}"

    redeems.insert_one({
        "_id": redeem_id,
        "user": user["_id"],
        "type": redeem_type,
        "plan": plan["title"] if plan else "Custom",
        "amount": plan["amount"] if plan else 0,
        "points": plan["points"] if plan else user["points"],
        "input": text,
        "status": "pending",
        "time": time.time()
    })

    await update.message.reply_text(
        "✅ *Redeem Request Submitted*\n\n"
        "Admin verify karke manually fulfill karega.",
        parse_mode="Markdown"
    )

    context.user_data.clear()

# =================================================
# SIMPLE REDEEM (REWARD)
# =================================================
async def create_simple_redeem(update, context, rtype):
    q = update.callback_query
    await q.answer()

    db = context.application.bot_data["db"]
    users = db.users
    redeems = db.redeems

    user = users.find_one({"_id": q.from_user.id})

    if not user or user["points"] <= 0:
        await q.message.edit_text("❌ Insufficient points.")
        return

    redeem_id = f"redeem_{int(time.time())}"

    redeems.insert_one({
        "_id": redeem_id,
        "user": user["_id"],
        "type": rtype,
        "points": user["points"],
        "status": "pending",
        "time": time.time()
    })

    await q.message.edit_text(
        f"✅ *{rtype} Redeem Submitted*\n\nAdmin will contact you.",
        parse_mode="Markdown"
)
