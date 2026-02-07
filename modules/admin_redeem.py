from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

# ================= ADMIN REDEEM LIST =================
async def admin_redeems(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != context.application.bot_data["ADMIN_ID"]:
        return

    db = context.application.bot_data["db"]
    redeems = db.redeems

    kb = []
    for r in redeems.find({"status": "pending"}):
        kb.append([
            InlineKeyboardButton(
                f"{r['type']} | {r['points']} pts",
                callback_data=f"redeem_view_{r['_id']}"
            )
        ])

    if not kb:
        await update.message.reply_text("✅ No pending redeem requests.")
        return

    await update.message.reply_text(
        "📋 *Pending Redeem Requests*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ================= VIEW REDEEM =================
async def redeem_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    rid = q.data.replace("redeem_view_", "")
    db = context.application.bot_data["db"]
    redeems = db.redeems

    r = redeems.find_one({"_id": rid})
    if not r:
        await q.message.edit_text("❌ Redeem request not found.")
        return

    kb = [[
        InlineKeyboardButton("✅ Approve", callback_data=f"redeem_ok_{rid}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"redeem_rej_{rid}")
    ]]

    await q.message.edit_text(
    "🧾 *Redeem Details*\n\n"
    f"👤 User ID: `{r['user']}`\n"
    f"🎁 Type: {r['type']}\n"
    f"📦 Plan: {r.get('plan','-')}\n"
    f"💰 Amount: ₹{r.get('amount',0)}\n"
    f"🎯 Points: {r['points']}\n"
    f"📞 Mobile / UPI: `{r.get('input','-')}`",
    parse_mode=ParseMode.MARKDOWN,
    reply_markup=InlineKeyboardMarkup(kb)
)

# ================= APPROVE =================
async def redeem_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    rid = q.data.replace("redeem_ok_", "")
    db = context.application.bot_data["db"]

    redeems = db.redeems
    users = db.users

    r = redeems.find_one({"_id": rid})
    if not r or r["status"] != "pending":
        await q.message.edit_text("⚠️ Already processed.")
        return

    # ✅ AUTO POINT DEDUCTION
    users.update_one(
        {"_id": r["user"]},
        {"$inc": {"points": -r["points"]}}
    )

    redeems.update_one(
        {"_id": rid},
        {"$set": {"status": "approved"}}
    )

    await context.bot.send_message(
        r["user"],
        "🎉 *Redeem Approved!*\n\n"
        "Admin ne aapka redeem approve kar diya hai.\n"
        "Reward / cash jald hi milega 💰",
        parse_mode=ParseMode.MARKDOWN,
    )

    await q.message.edit_text("✅ Redeem approved & points deducted.")

# ================= REJECT =================
async def redeem_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    rid = q.data.replace("redeem_rej_", "")
    db = context.application.bot_data["db"]
    redeems = db.redeems   # ✅ FIXED

    r = redeems.find_one({"_id": rid})
    if not r or r["status"] != "pending":
        await q.message.edit_text("⚠️ Already processed.")
        return

    redeems.update_one(
        {"_id": rid},
        {"$set": {"status": "rejected"}}
    )

    await q.message.edit_text("❌ Redeem rejected.")
