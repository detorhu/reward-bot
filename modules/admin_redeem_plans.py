from telegram import Update
from telegram.ext import ContextTypes
import time

# ================= ADD RECHARGE =================
async def addrecharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != context.application.bot_data["ADMIN_ID"]:
        return

    # /addrecharge Vi_1GB 19 100
    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage:\n/addrecharge <title> <amount₹> <points>\n"
            "Example:\n/addrecharge Vi_1GB 19 100"
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
        "active": True
    })

    await update.message.reply_text("✅ Recharge plan added")


# ================= DELETE RECHARGE =================
async def delrecharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != context.application.bot_data["ADMIN_ID"]:
        return

    if not context.args:
        await update.message.reply_text("Usage: /delrecharge <plan_id>")
        return

    pid = context.args[0]
    db = context.application.bot_data["db"]

    res = db.redeem_plans.update_one(
        {"_id": pid},
        {"$set": {"active": False}}
    )

    if res.matched_count:
        await update.message.reply_text("🗑️ Recharge plan disabled")
    else:
        await update.message.reply_text("❌ Plan not found")


# ================= ADD CASH =================
async def addcash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != context.application.bot_data["ADMIN_ID"]:
        return

    # /addcash 50 500
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage:\n/addcash <amount₹> <points>\n"
            "Example:\n/addcash 50 500"
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
        "active": True
    })

    await update.message.reply_text("✅ Cash option added")
