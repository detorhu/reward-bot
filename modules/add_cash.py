async def addcash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != context.application.bot_data["ADMIN_ID"]:
        return

    # /addcash 50 500
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage:\n/addcash <amount₹> <points>"
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
