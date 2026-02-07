from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from pymongo import MongoClient
import time
from modules.redeem import redeem_menu
from modules.reward import reward_menu
# ================= CONFIG =================
BOT_TOKEN = "8096328605:AAEsi9pXGY_5SK9-Y9TtZVh0SQv8W0zpMRE"
ADMIN_ID = 7066124462

MONGO_URI = "mongodb+srv://neonman242:deadman242@game0.sqfzcd4.mongodb.net/reward_bot?retryWrites=true&w=majority"
DB_NAME = "reward_bot"

REF_POINTS = 5
MIN_REWARD_POINTS = 100

UPI_ID = "avanishpal080@oksbi"
DEFAULT_QR = "https://raw.githubusercontent.com/detorhu/reward-bot/main/qr.png"
# =========================================

# ================= DB =====================
mongo = MongoClient(MONGO_URI)
db = mongo[DB_NAME]

users = db.users
rewards = db.rewards
products = db.products
orders = db.orders
settings = db.settings
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

def get_qr():
    s = settings.find_one({"_id": "qr"})
    return s["url"] if s else DEFAULT_QR

def set_qr(url):
    settings.update_one(
        {"_id": "qr"},
        {"$set": {"url": url}},
        upsert=True
    )
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
            InlineKeyboardButton("👤 Profile", callback_data="profile"),
            InlineKeyboardButton("🛒 Redeem", callback_data="redeem")
        ],
        [
            InlineKeyboardButton("💸 Reward", callback_data="reward"),
            InlineKeyboardButton("💎 Premium", callback_data="premium")
        ],
        [InlineKeyboardButton("🛒 Buy Products", callback_data="buy_menu")]
    ]

    await update.message.reply_text(
    "👋 *Welcome to Rewards Bot*\n\n"
    "🎁 Refer friends & earn points\n"
    "🛒 Redeem points for digital rewards\n"
    "💎 Premium available",
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

async def premium(update, context):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text("💎 Premium = 2x referral points\nPrice ₹199")
# ==========================================

# ================= BUY MENU =================
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

    if not kb:
        await q.message.reply_text("❌ No products available")
        return

    await q.message.reply_text(
        "🛒 *Select Product*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )
# ================= BUY PRODUCT ==============
async def buy_product(update, context):
    q = update.callback_query
    await q.answer()

    pid = q.data.replace("buy_prod_", "")
    p = products.find_one({"_id": pid})

    if not p:
        await q.message.reply_text("❌ Product not found or removed")
        return

    u = get_user(q.from_user.id)

    discount = min(u["points"], p["max_points_discount"])
    final_price = p["cash_price"] - discount

    oid = f"ord_{int(time.time())}"
    orders.insert_one({
        "_id": oid,
        "user": u["_id"],
        "product": p["name"],
        "price": final_price,
        "discount": discount,
        "status": "pending"
    })

    # ✅ POINTS DEDUCT (INSIDE FUNCTION)
    if discount > 0:
        users.update_one(
            {"_id": u["_id"]},
            {"$inc": {"points": -discount}}
        )

    kb = [[InlineKeyboardButton("✅ I Have Paid", callback_data=f"paid_{oid}")]]

    await q.message.reply_text(
    (
        f"🛒 *Order Created*\n\n"
        f"📦 Product: {p['name']}\n"
        f"💰 Price: ₹{p['cash_price']}\n"
        f"🎯 Discount: ₹{discount}\n"
        f"✅ Final Pay: ₹{final_price}\n\n"
        f"UPI ID: `{UPI_ID}`\n\n"
        f"Payment ke baad *I Have Paid* dabaye"
    ),
    parse_mode="Markdown",
    reply_markup=InlineKeyboardMarkup(kb)
    )

# ================= PAYMENT =================
async def paid(update, context):
    q = update.callback_query
    await q.answer()

    oid = q.data.replace("paid_", "")
    o = orders.find_one({"_id": oid})

    if not o or o["status"] != "pending":
        await q.message.reply_text("❌ Invalid order")
        return

    orders.update_one({"_id": oid}, {"$set": {"status": "submitted"}})
    await q.message.reply_text("✅ Payment submitted. Await admin approval")

    await context.bot.send_message(
        ADMIN_ID,
        f"🧾 New payment submitted\nOrder ID: {oid}"
    )
# ==========================================

# ================= ADMIN ===================
async def admin_orders(update, context):
    if not is_admin(update.effective_user.id):
        return

    kb = []
    for o in orders.find({"status": "submitted"}):
        kb.append([
            InlineKeyboardButton(
                f"{o['product']} ₹{o['price']}",
                callback_data=f"adm_{o['_id']}"
            )
        ])

    await update.message.reply_text(
        "📋 Pending Orders",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def admin_view(update, context):
    q = update.callback_query
    await q.answer()

    oid = q.data.replace("adm_", "")
    kb = [[
        InlineKeyboardButton("✅ Approve", callback_data=f"ok_{oid}"),
        InlineKeyboardButton("❌ Reject + Refund", callback_data=f"rej_{oid}")
    ]]

    await q.message.reply_text(
        "Approve this order?",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def approve(update, context):
    q = update.callback_query
    await q.answer()

    oid = q.data.replace("ok_", "")
    o = orders.find_one({"_id": oid})

    if not o or o["status"] != "submitted":
        await q.message.reply_text("Already processed")
        return

    orders.update_one({"_id": oid}, {"$set": {"status": "approved"}})
    await q.message.reply_text("✅ Approved. Use /sendkey <order_id> KEY")

async def reject(update, context):
    q = update.callback_query
    await q.answer()

    oid = q.data.replace("rej_", "")
    o = orders.find_one({"_id": oid})

    if o:
        users.update_one(
            {"_id": o["user"]},
            {"$inc": {"points": o["discount"]}}
        )

    orders.update_one({"_id": oid}, {"$set": {"status": "rejected"}})
    await q.message.reply_text("❌ Rejected & points refunded")

async def sendkey(update, context):
    if not is_admin(update.effective_user.id):
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /sendkey <order_id> KEY")
        return

    oid = context.args[0]
    key = " ".join(context.args[1:])
    o = orders.find_one({"_id": oid})

    await context.bot.send_message(o["user"], f"🔑 Your Key:\n{key}")
    orders.update_one({"_id": oid}, {"$set": {"status": "delivered"}})
# ==========================================

# ================= ADD PRODUCT =============
async def addproduct(update, context):
    if not is_admin(update.effective_user.id):
        return

    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage:\n/addproduct <name> <price> <max_discount>"
        )
        return

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
    await update.message.reply_text("✅ Product added")
# ==========================================

# ================= SET QR ==================
async def setqr(update, context):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("Usage: /setqr <RAW_IMAGE_URL>")
        return

    set_qr(context.args[0])
    await update.message.reply_text("✅ QR updated")

# ==========================================

# ================= MAIN ====================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("adminorders", admin_orders))
app.add_handler(CommandHandler("sendkey", sendkey))
app.add_handler(CommandHandler("addproduct", addproduct))
app.add_handler(CommandHandler("setqr", setqr))

app.add_handler(CallbackQueryHandler(referral, "^ref$"))
app.add_handler(CallbackQueryHandler(redeem_menu, "^redeem$"))
app.add_handler(CallbackQueryHandler(reward_menu, "^reward$"))
app.add_handler(CallbackQueryHandler(premium, "^premium$"))
app.add_handler(CallbackQueryHandler(buy_menu, "^buy_menu$"))
app.add_handler(CallbackQueryHandler(buy_product, r"^buy_prod_"))
app.add_handler(CallbackQueryHandler(paid, "^paid_"))
app.add_handler(CallbackQueryHandler(admin_view, "^adm_"))
app.add_handler(CallbackQueryHandler(approve, "^ok_"))
app.add_handler(CallbackQueryHandler(reject, "^rej_"))
app.add_handler(CallbackQueryHandler(profile_menu, "^profile$"))
app.add_handler(CallbackQueryHandler(profile_orders, "^profile_orders$"))
app.add_handler(CallbackQueryHandler(profile_referrals, "^profile_referrals$"))

print("✅ BOT RUNNING")
app.run_polling()
