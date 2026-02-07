from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from pymongo import MongoClient
import time

# ================= CONFIG =================
BOT_TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 7066124462

MONGO_URI = "YOUR_MONGO_URI"
DB_NAME = "reward_bot"

REF_POINTS = 5
MIN_REWARD_POINTS = 100

UPI_ID = "yourupi@upi"
QR_IMAGE_URL = "https://example.com/qr.png"
# =========================================

# ================= DB =====================
mongo = MongoClient(MONGO_URI)
db = mongo[DB_NAME]

users = db.users
rewards = db.rewards
products = db.products
orders = db.orders
# =========================================

# ================= HELPERS =================
def is_admin(uid):
    return uid == ADMIN_ID

def get_user(uid, username=None):
    user = users.find_one({"_id": uid})
    if not user:
        user = {
            "_id": uid,
            "username": username,
            "points": 0,
            "referrals": 0,
            "referred_by": None,
            "joined": time.time()
        }
        users.insert_one(user)
    return user
# ==========================================

# ================= START ===================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    user = get_user(u.id, u.username)

    if context.args:
        try:
            ref = int(context.args[0])
            if ref != u.id and user["referred_by"] is None:
                get_user(ref)
                users.update_one({"_id": u.id}, {"$set": {"referred_by": ref}})
                users.update_one(
                    {"_id": ref},
                    {"$inc": {"points": REF_POINTS, "referrals": 1}}
                )
        except:
            pass

    kb = [
        [InlineKeyboardButton("🔗 Referral", callback_data="ref")],
        [
            InlineKeyboardButton("💰 Balance", callback_data="bal"),
            InlineKeyboardButton("🛒 Redeem", callback_data="redeem")
        ],
        [
            InlineKeyboardButton("💸 Reward", callback_data="reward"),
            InlineKeyboardButton("💎 Premium", callback_data="premium")
        ],
        [InlineKeyboardButton("🛒 Buy Products", callback_data="buy_menu")]
    ]

    await update.message.reply_text(
        "👋 *Welcome to Rewards Bot*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )
# ==========================================

# ================= BASIC ===================
async def referral(update, context):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text(
        f"https://t.me/{context.bot.username}?start={q.from_user.id}"
    )

async def balance(update, context):
    q = update.callback_query
    await q.answer()
    u = get_user(q.from_user.id)
    await q.message.reply_text(
        f"Points: {u['points']}\nReferrals: {u['referrals']}"
    )

async def premium(update, context):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text("Premium = 2x referral points\nPrice ₹199")
# ==========================================

# ================= REWARD =================
async def reward(update, context):
    q = update.callback_query
    await q.answer()
    u = get_user(q.from_user.id)

    if u["points"] < MIN_REWARD_POINTS:
        await q.message.reply_text("Need 100 points")
        return

    users.update_one({"_id": u["_id"]}, {"$inc": {"points": -MIN_REWARD_POINTS}})
    rewards.insert_one({"user": u["_id"], "amount": 50, "status": "pending"})

    await q.message.reply_text("Reward requested")
    await context.bot.send_message(ADMIN_ID, f"Reward request from {u['_id']}")
# ==========================================

# ================= REDEEM =================
async def redeem(update, context):
    q = update.callback_query
    await q.answer()
    kb = [
        [InlineKeyboardButton("🔑 1 Day – 20 pts", callback_data="rd_20")],
        [InlineKeyboardButton("🔑 7 Day – 80 pts", callback_data="rd_80")],
        [InlineKeyboardButton("🤖 Premium Bot – 150 pts", callback_data="rd_150")]
    ]
    await q.message.reply_text("Redeem:", reply_markup=InlineKeyboardMarkup(kb))

async def redeem_do(update, context):
    q = update.callback_query
    cost = int(q.data.split("_")[1])
    u = get_user(q.from_user.id)

    if u["points"] < cost:
        await q.answer("Not enough points", show_alert=True)
        return

    users.update_one({"_id": u["_id"]}, {"$inc": {"points": -cost}})
    await q.message.reply_text("Redeem successful (admin will deliver)")
# ==========================================

# ================= BUY ====================
async def buy_menu(update, context):
    q = update.callback_query
    await q.answer()

    kb = []
    for p in products.find({"active": True}):
        kb.append([
            InlineKeyboardButton(
                f"{p['name']} – ₹{p['cash_price']}",
                callback_data=f"buy_prod_{p['_id']}"
            )
        ])

    await q.message.reply_text("Products:", reply_markup=InlineKeyboardMarkup(kb))

async def buy_product(update, context):
    q = update.callback_query
    await q.answer()

    pid = q.data.replace("buy_prod_", "")
    p = products.find_one({"_id": pid})
    u = get_user(q.from_user.id)

    discount = min(u["points"], p["max_points_discount"])
    final = p["cash_price"] - discount

    users.update_one({"_id": u["_id"]}, {"$inc": {"points": -discount}})

    oid = f"ord_{int(time.time())}"
    orders.insert_one({
        "_id": oid,
        "user": u["_id"],
        "product": p["name"],
        "price": final,
        "discount": discount,
        "status": "pending"
    })

    kb = [[InlineKeyboardButton("I Have Paid", callback_data=f"paid_{oid}")]]
    await q.message.reply_photo(
        QR_IMAGE_URL,
        caption=f"Pay ₹{final}\nUPI: {UPI_ID}",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def paid(update, context):
    q = update.callback_query
    await q.answer()
    oid = q.data.replace("paid_", "")
    orders.update_one({"_id": oid}, {"$set": {"status": "submitted"}})
    await q.message.reply_text("Payment submitted")
    await context.bot.send_message(ADMIN_ID, f"New payment {oid}")
# ==========================================

# ================= ADMIN ==================
async def admin_orders(update, context):
    if not is_admin(update.effective_user.id): return
    kb = []
    for o in orders.find({"status": "submitted"}):
        kb.append([InlineKeyboardButton(o["product"], callback_data=f"adm_{o['_id']}")])
    await update.message.reply_text("Orders:", reply_markup=InlineKeyboardMarkup(kb))

async def admin_view(update, context):
    q = update.callback_query
    await q.answer()
    oid = q.data.replace("adm_", "")
    kb = [[
        InlineKeyboardButton("Approve", callback_data=f"ok_{oid}"),
        InlineKeyboardButton("Reject + Refund", callback_data=f"rej_{oid}")
    ]]
    await q.message.reply_text("Approve?", reply_markup=InlineKeyboardMarkup(kb))

async def approve(update, context):
    q = update.callback_query
    await q.answer()
    oid = q.data.replace("ok_", "")
    orders.update_one({"_id": oid}, {"$set": {"status": "approved"}})
    await q.message.reply_text("Approved. Use /sendkey <order_id> KEY")

async def reject(update, context):
    q = update.callback_query
    await q.answer()
    oid = q.data.replace("rej_", "")
    o = orders.find_one({"_id": oid})
    if o:
        users.update_one({"_id": o["user"]}, {"$inc": {"points": o["discount"]}})
    orders.update_one({"_id": oid}, {"$set": {"status": "rejected"}})
    await q.message.reply_text("Rejected & points refunded")

async def sendkey(update, context):
    if not is_admin(update.effective_user.id): return
    oid = context.args[0]
    key = " ".join(context.args[1:])
    o = orders.find_one({"_id": oid})
    await context.bot.send_message(o["user"], f"Your Key:\n{key}")
    orders.update_one({"_id": oid}, {"$set": {"status": "delivered"}})

# ================= ADD PRODUCT ============
async def addproduct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    name = context.args[0]
    price = int(context.args[1])
    discount = int(context.args[2])
    products.insert_one({
        "_id": f"prod_{int(time.time())}",
        "name": name,
        "cash_price": price,
        "max_points_discount": discount,
        "active": True
    })
    await update.message.reply_text("Product added")
# ==========================================

# ================= MAIN ====================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("adminorders", admin_orders))
app.add_handler(CommandHandler("sendkey", sendkey))
app.add_handler(CommandHandler("addproduct", addproduct))

app.add_handler(CallbackQueryHandler(referral, "^ref$"))
app.add_handler(CallbackQueryHandler(balance, "^bal$"))
app.add_handler(CallbackQueryHandler(redeem, "^redeem$"))
app.add_handler(CallbackQueryHandler(redeem_do, "^rd_"))
app.add_handler(CallbackQueryHandler(reward, "^reward$"))
app.add_handler(CallbackQueryHandler(premium, "^premium$"))
app.add_handler(CallbackQueryHandler(buy_menu, "^buy_menu$"))
app.add_handler(CallbackQueryHandler(buy_product, "^buy_prod_"))
app.add_handler(CallbackQueryHandler(paid, "^paid_"))
app.add_handler(CallbackQueryHandler(admin_view, "^adm_"))
app.add_handler(CallbackQueryHandler(approve, "^ok_"))
app.add_handler(CallbackQueryHandler(reject, "^rej_"))

print("✅ BOT RUNNING")
app.run_polling()
