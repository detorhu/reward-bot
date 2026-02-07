from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, ContextTypes
)
from pymongo import MongoClient
import time

# ================= CONFIG =================
BOT_TOKEN = "8096328605:AAEsi9pXGY_5SK9-Y9TtZVh0SQv8W0zpMRE"
ADMIN_ID = 7066124462
MONGO_URI = "mongodb+srv://neonman242:deadman242@game0.sqfzcd4.mongodb.net/reward_bot?retryWrites=true&w=majority"
DB_NAME = "reward_bot"

REF_POINTS = 5
PREMIUM_MULTIPLIER = 2
MIN_REWARD_POINTS = 100
# =========================================

# ================= DB =====================
mongo = MongoClient(MONGO_URI)
db = mongo[DB_NAME]
users = db.users
rewards = db.rewards
ads = db.ads
# =========================================


# ================= HELPERS =================
def get_user(uid, username=None):
    user = users.find_one({"_id": uid})
    if not user:
        user = {
            "_id": uid,
            "username": username,
            "points": 0,
            "referrals": 0,
            "referred_by": None,
            "premium": False,
            "joined": time.time()
        }
        users.insert_one(user)
    return user


def add_points(uid, amount):
    users.update_one({"_id": uid}, {"$inc": {"points": amount}})


def is_admin(uid):
    return uid == ADMIN_ID
# ==========================================


# ================= START ===================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    data = get_user(uid, user.username)

    if context.args:
        try:
            ref = int(context.args[0])
            if ref != uid and data["referred_by"] is None:
                users.update_one({"_id": uid}, {"$set": {"referred_by": ref}})
                ref_user = get_user(ref)
                bonus = REF_POINTS * (PREMIUM_MULTIPLIER if ref_user["premium"] else 1)
                add_points(ref, bonus)
                users.update_one({"_id": ref}, {"$inc": {"referrals": 1}})
        except:
            pass

    kb = [
        [InlineKeyboardButton("🔗 Get Referral Link", callback_data="get_ref")]
    ]

    text = (
        "👋 *Welcome to Rewards Bot*\n\n"
        "🎁 Refer friends & earn points\n"
        "🛒 Redeem points for digital rewards\n"
        "💎 Premium available\n\n"
        "👇 Use the button below:"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )
# ==========================================


# ================= INLINE REF BUTTON ======
async def referral_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    link = f"https://t.me/{context.bot.username}?start={uid}"

    await q.message.reply_text(
        f"🔗 *Your Referral Link:*\n{link}\n\n"
        "Share this link with friends 👥",
        parse_mode="Markdown"
    )
# ==========================================


# ================= REFER (COMMAND BACKUP) ==
async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    link = f"https://t.me/{context.bot.username}?start={uid}"
    await update.message.reply_text(
        f"🔗 *Your Referral Link:*\n{link}",
        parse_mode="Markdown"
    )
# ==========================================


# ================= BALANCE =================
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    await update.message.reply_text(
        f"💰 *Points:* {u['points']}\n"
        f"👥 *Referrals:* {u['referrals']}\n"
        f"💎 *Premium:* {'Yes' if u['premium'] else 'No'}",
        parse_mode="Markdown"
    )
# ==========================================


# ================= REDEEM ==================
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🔑 1 Day Key – 20 pts", callback_data="redeem_20")],
        [InlineKeyboardButton("🔑 7 Day Key – 80 pts", callback_data="redeem_80")],
        [InlineKeyboardButton("🤖 Premium Bot – 150 pts", callback_data="redeem_150")]
    ]
    await update.message.reply_text(
        "🛒 *Redeem Store*\nChoose reward:",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )


async def redeem_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    cost = int(q.data.split("_")[1])
    user = get_user(uid)

    if user["points"] < cost:
        await q.answer("Not enough points", show_alert=True)
        return

    users.update_one({"_id": uid}, {"$inc": {"points": -cost}})

    await q.message.reply_text("✅ Redeem request sent.\nAdmin will deliver shortly.")

    await context.bot.send_message(
        ADMIN_ID,
        f"🛒 *Redeem Request*\nUser: `{uid}`\nCost: {cost} points",
        parse_mode="Markdown"
    )
# ==========================================


# ================= CASH REWARD =============
async def reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = get_user(uid)

    if user["points"] < MIN_REWARD_POINTS:
        await update.message.reply_text(
            "❌ Minimum 100 points required.\nRewards are subject to verification."
        )
        return

    users.update_one({"_id": uid}, {"$inc": {"points": -MIN_REWARD_POINTS}})
    rewards.insert_one({
        "user_id": uid,
        "amount": 50,
        "time": time.time(),
        "status": "pending"
    })

    await update.message.reply_text("✅ Reward request submitted.\n⏳ Manual review in progress.")

    await context.bot.send_message(
        ADMIN_ID,
        f"💸 *Reward Request*\nUser: `{uid}`\nAmount: ₹50",
        parse_mode="Markdown"
    )
# ==========================================


# ================= PREMIUM =================
async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💎 *Premium Plan*\n\n"
        "✔️ 2x referral points\n"
        "✔️ Faster rewards\n"
        "✔️ Premium bot access\n\n"
        "Price: ₹199 / month\n"
        "Contact admin to activate",
        parse_mode="Markdown"
    )


async def addpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    uid = int(context.args[0])
    users.update_one({"_id": uid}, {"$set": {"premium": True}})
    await update.message.reply_text("✅ Premium activated")
# ==========================================


# ================= ADS =====================
async def addad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    text = " ".join(context.args)
    ads.insert_one({"text": text})
    await update.message.reply_text("✅ Ad added")
# ==========================================


# ================= STATS ===================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(
        f"👥 Users: {users.count_documents({})}\n"
        f"🟡 Pending rewards: {rewards.count_documents({'status':'pending'})}"
    )
# ==========================================


# ================= MAIN ====================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("refer", refer))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("redeem", redeem))
app.add_handler(CallbackQueryHandler(redeem_callback, pattern="^redeem_"))
app.add_handler(CallbackQueryHandler(referral_button, pattern="^get_ref$"))
app.add_handler(CommandHandler("reward", reward))
app.add_handler(CommandHandler("premium", premium))
app.add_handler(CommandHandler("addpremium", addpremium))
app.add_handler(CommandHandler("addad", addad))
app.add_handler(CommandHandler("stats", stats))

print("✅ Reward Bot with MongoDB Running")
app.run_polling()
# ==========================================
