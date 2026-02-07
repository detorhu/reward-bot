from telegram import Update
from telegram.ext import ContextTypes
import time

# =================================================
# ADD RECHARGE PLAN
# =================================================
async def addrecharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != context.application.bot_data["ADMIN_ID"]:
        return

    # /addrecharge Vi_1GB 19 100
    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage:\n"
            "/addrecharge <title> <amount₹> <points>\n\n"
            "Example:\n"
            "/addrecharge Vi_1GB 19 100"
        )
        return

    title = context.args[0].replace("_", " ")
    amount = int(context.args[1])
    points = int(context.args[2])

    db = context.application.bot_data["db"]

    db.redeem_plans.insert_one({
        "_id": f"recharge_{int(time.time())}",
        "type": "recharge",
        "title": title,
        "amount": amount,
        "points": points,
        "active": True,
        "time": time.time()
    })

    await update.message.reply_text("✅ Recharge plan added successfully")


# =================================================
# DELETE / DISABLE RECHARGE OR CASH PLAN
# =================================================
async def delrecharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != context.application.bot_data["ADMIN_ID"]:
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "/delrecharge <plan_id>\n\n"
            "Example:\n"
            "/delrecharge recharge_123456"
        )
        return

    plan_id = context.args[0]
    db = context.application.bot_data["db"]

    res = db.redeem_plans.update_one(
        {"_id": plan_id},
        {"$set": {"active": False}}
    )

    if res.matched_count:
        await update.message.reply_text("🗑️ Plan disabled successfully")
    else:
        await update.message.reply_text("❌ Plan ID not found")


# =================================================
# ADD CASH / UPI OPTION
# =================================================
async def addcash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != context.application.bot_data["ADMIN_ID"]:
        return

    # /addcash 50 500
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage:\n"
            "/addcash <amount₹> <points>\n\n"
            "Example:\n"
            "/addcash 50 500"
        )
        return

    amount = int(context.args[0])
    points = int(context.args[1])

    db = context.application.bot_data["db"]

    db.redeem_plans.insert_one({
        "_id": f"cash_{int(time.time())}",
        "type": "cash",
        "title": f"₹{amount} Cash",
        "amount": amount,
        "points": points,
        "active": True,
        "time": time.time()
    })

    await update.message.reply_text("✅ Cash option added successfully")


# =================================================
# LIST RECHARGE PLANS (FOR PLAN ID)
# =================================================
async def listrecharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != context.application.bot_data["ADMIN_ID"]:
        return

    db = context.application.bot_data["db"]
    plans = db.redeem_plans.find({"type": "recharge"})

    text = "📱 *RECHARGE PLANS*\n\n"
    count = 0

    for p in plans:
        count += 1
        status = "🟢 ACTIVE" if p.get("active") else "🔴 DISABLED"

        text += (
            f"{count}️⃣ *{p['title']}*\n"
            f"💰 Amount: ₹{p['amount']}\n"
            f"🎯 Points: {p['points']}\n"
            f"🆔 ID: `{p['_id']}`\n"
            f"📌 Status: {status}\n\n"
        )

    if count == 0:
        text = "❌ No recharge plans found."

    await update.message.reply_text(text, parse_mode="Markdown")


# =================================================
# LIST CASH / UPI PLANS
# =================================================
async def listcash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != context.application.bot_data["ADMIN_ID"]:
        return

    db = context.application.bot_data["db"]
    plans = db.redeem_plans.find({"type": "cash"})

    text = "💵 *CASH / UPI PLANS*\n\n"
    count = 0

    for p in plans:
        count += 1
        status = "🟢 ACTIVE" if p.get("active") else "🔴 DISABLED"

        text += (
            f"{count}️⃣ *₹{p['amount']} Cash*\n"
            f"🎯 Points: {p['points']}\n"
            f"🆔 ID: `{p['_id']}`\n"
            f"📌 Status: {status}\n\n"
        )

    if count == 0:
        text = "❌ No cash plans found."

    await update.message.reply_text(text, parse_mode="Markdown")
