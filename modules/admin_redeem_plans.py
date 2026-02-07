async def addrecharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != context.application.bot_data["ADMIN_ID"]:
        return

    # /addrecharge Vi_1GB 19 100
    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage:\n/addrecharge <title> <amount₹> <points>"
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
