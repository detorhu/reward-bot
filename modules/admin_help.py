from telegram import Update
from telegram.ext import ContextTypes

ADMIN_ID = 7066124462  # 🔒 HARD CODED OWNER

# ================= ADMIN HELP =================
async def adminhelp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return  # ❌ owner only

    text = (
        "👑 <b>ADMIN HELP PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "📦 <b>ORDER MANAGEMENT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 <b>/adminorders</b>\n"
        "   • Pending paid orders list\n\n"
        "🔹 Inline buttons:\n"
        "   • <code>adm_&lt;order_id&gt;</code> → view order\n"
        "   • <code>ok_&lt;order_id&gt;</code> → approve\n"
        "   • <code>rej_&lt;order_id&gt;</code> → reject + refund\n\n"
        "🔹 <b>/sendkey &lt;order_id&gt; KEY</b>\n"
        "   • Deliver product key\n\n"

        "🎁 <b>REDEEM MANAGEMENT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 <b>/adminredeems</b>\n"
        "   • View all pending redeem requests\n\n"
        "🔹 Inline actions:\n"
        "   • <code>redeem_view_&lt;id&gt;</code>\n"
        "   • <code>redeem_ok_&lt;id&gt;</code>\n"
        "   • <code>redeem_rej_&lt;id&gt;</code>\n\n"
        "📌 Redeem is <b>100% manual</b>\n\n"

        "🛒 <b>PRODUCT MANAGEMENT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 <b>/addproduct &lt;name&gt; &lt;price&gt; &lt;max_discount&gt;</b>\n"
        "🔹 <b>/delproduct &lt;product_id&gt;</b>\n"
        "🔹 <b>/products</b>\n\n"

        "🖼️ <b>SYSTEM</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 <b>/setqr &lt;image_url&gt;</b>\n\n"

        "📱 <b>RECHARGE PLANS</b>\n"
        "━━━━━━━━━━━━━━\n"
        "➕ <code>/addrecharge Vi_1GB 19 100</code>\n"
        "❌ <code>/delrecharge &lt;plan_id&gt;</code>\n\n"

        "💵 <b>CASH / UPI</b>\n"
        "━━━━━━━━━━━━━━\n"
        "➕ <code>/addcash 50 500</code>\n\n"

        "⚠️ <b>IMPORTANT</b>\n"
        "━━━━━━━━━━━━━━\n"
        "✔ Admin decision final\n"
        "✔ Manual verification\n"
        "✔ Abuse = reject\n\n"

        "✅ <b>SYSTEM STATUS: ACTIVE</b>"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML"
    )
