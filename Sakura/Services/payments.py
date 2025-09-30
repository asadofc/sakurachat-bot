import random
import asyncio
import aiohttp
import orjson
from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from Sakura.Core.config import BOT_TOKEN
from Sakura.Core.helpers import fetch_user, log_action, get_error
from Sakura.Core.logging import logger
from Sakura.Services.tracking import track_user
from Sakura.Interface.effects import animate_reaction, add_reaction, send_effect, EFFECTS
from Sakura.Interface.reactions import EMOJI_REACT
from Sakura.Interface.typing import send_typing
from Sakura.Interface.messages import INVOICE_DESCRIPTIONS, THANK_YOU_MESSAGES, REFUND_MESSAGES
from Sakura.Database.database import save_purchase, get_purchases
from Sakura.Database.constants import PAYMENT_STICKERS
from Sakura import state

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send an invoice for sakura flowers."""
    try:
        user_info = fetch_user(update.message)
        log_action("INFO", "🌸 /buy command received", user_info)
        track_user(update, user_info)

        if EMOJI_REACT:
            try:
                random_emoji = random.choice(EMOJI_REACT)
                if state.effects_client and update.effective_chat.type == "private":
                    await animate_reaction(
                        update.effective_chat.id,
                        update.message.message_id,
                        random_emoji
                    )
                else:
                    await add_reaction(context, update, random_emoji, user_info)
            except Exception as e:
                log_action("WARNING", f"⚠️ Failed to add emoji reaction: {e}", user_info)

        await send_typing(context, update.effective_chat.id, user_info)

        amount = 50
        if len(update.message.text.split()) > 1 and update.message.text.split()[1].isdigit():
            amount = int(update.message.text.split()[1])
            if amount > 100000:
                amount = 100000
            elif amount < 1:
                amount = 1

        await send_invoice(context, update.message.chat.id, user_info, amount)

    except Exception as e:
        user_info = fetch_user(update.message)
        log_action("ERROR", f"❌ Error sending invoice: {e}", user_info)
        await update.message.reply_text("❌ Oops! Something went wrong creating the invoice. Try again later! 🔧")

async def buyers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all flower buyers with their donation amounts."""
    try:
        user_info = fetch_user(update.message)
        log_action("INFO", "💝 /buyers command received", user_info)
        track_user(update, user_info)

        if EMOJI_REACT:
            try:
                random_emoji = random.choice(EMOJI_REACT)
                if state.effects_client and update.effective_chat.type == "private":
                    if not await animate_reaction(update.effective_chat.id, update.message.message_id, random_emoji):
                        await add_reaction(context, update, random_emoji, user_info)
                else:
                    await add_reaction(context, update, random_emoji, user_info)
            except Exception as e:
                log_action("WARNING", f"⚠️ Failed to add emoji reaction: {e}", user_info)

        await send_typing(context, update.effective_chat.id, user_info)
        purchases = await get_purchases()

        if not purchases:
            no_buyers_text = (
                "🌸 <b>Flower Buyers</b>\n\n"
                "No one has bought flowers yet! Be the first to support with /buy 💝"
            )
            if update.message.chat.type == "private":
                if not await send_effect(update.message.chat.id, no_buyers_text):
                    await update.message.reply_text(no_buyers_text, parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text(no_buyers_text, parse_mode=ParseMode.HTML)
            return

        buyers_text = "🌸 <b>Flower Buyers</b>\n\n"
        buyers_text += "💝 <i>Thank you to all our wonderful supporters!</i>\n\n"
        for i, purchase in enumerate(purchases, 1):
            user_mention = f'<a href="tg://user?id={purchase["user_id"]}">{purchase["first_name"] or "Anonymous"}</a>'
            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            buyers_text += f"{rank_emoji} {user_mention} - {purchase['total_amount']} ⭐"
            if purchase['purchase_count'] > 1:
                buyers_text += f" ({purchase['purchase_count']} purchases)"
            buyers_text += "\n"
        buyers_text += f"\n🌸 <i>Total buyers: {len(purchases)}</i>"

        if update.message.chat.type == "private":
            if not await send_effect(update.message.chat.id, buyers_text):
                await update.message.reply_text(buyers_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        else:
            await update.message.reply_text(buyers_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    except Exception as e:
        user_info = fetch_user(update.message)
        log_action("ERROR", f"❌ Error in buyers command: {e}", user_info)
        await update.message.reply_text(get_error())

async def send_invoice(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_info: dict, amount: int):
    """Sends a payment invoice."""
    try:
        if user_info["chat_type"] == "private" and state.effects_client:
            try:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendInvoice"
                payload = {
                    'chat_id': chat_id,
                    'title': "Flowers 🌸",
                    'description': random.choice(INVOICE_DESCRIPTIONS),
                    'payload': f"sakura_star_{user_info['user_id']}",
                    'provider_token': "",
                    'currency': "XTR",
                    'prices': [{'label': '✨ Sakura Star', 'amount': amount}],
                    'message_effect_id': random.choice(EFFECTS)
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, data=orjson.dumps(payload),
                                            headers={'Content-Type': 'application/json'}) as response:
                        if (await response.json()).get('ok'):
                            log_action("INFO", f"✨ Invoice with effects sent for {amount} stars", user_info)
                            return
            except Exception:
                log_action("WARNING", "⚠️ Invoice with effects failed, falling back to normal.", user_info)

        await context.bot.send_invoice(
            chat_id=chat_id,
            title="Flowers 🌸",
            description=random.choice(INVOICE_DESCRIPTIONS),
            payload=f"sakura_star_{user_info['user_id']}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label='✨ Sakura Star', amount=amount)]
        )
        log_action("INFO", f"✅ Invoice sent for {amount} stars", user_info)

    except Exception as e:
        log_action("ERROR", f"❌ Error sending invoice: {e}", user_info)
        await context.bot.send_message(chat_id, "❌ Oops! Something went wrong creating the invoice. Try again later! 🔧")

async def precheckout_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Answer the PreCheckoutQuery."""
    query = update.pre_checkout_query
    await context.bot.answer_pre_checkout_query(
        pre_checkout_query_id=query.id,
        ok=True
    )
    logger.info(f"💳 Pre-checkout approved for user {query.from_user.id}")

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle successful payment - refund if 10 stars or less, otherwise process normally."""
    payment = update.message.successful_payment
    user_id = update.message.from_user.id
    amount = payment.total_amount
    user_info = fetch_user(update.message)

    log_action("INFO", f"💰 Payment received for {amount} stars", user_info)

    if amount > 10:
        save_purchase(
            user_id=user_id,
            username=user_info.get("username"),
            first_name=user_info.get("first_name"),
            last_name=user_info.get("last_name"),
            amount=amount,
            charge_id=payment.telegram_payment_charge_id
        )

    if amount <= 10:
        log_action("INFO", f"🔄 Refunding payment of {amount} stars (kindness gesture)", user_info)
        await asyncio.sleep(4)
        state.payment_storage[payment.telegram_payment_charge_id] = {
            'user_id': user_id,
            'amount': amount,
            'charge_id': payment.telegram_payment_charge_id
        }
        try:
            await context.bot.refund_star_payment(
                user_id=user_id,
                telegram_payment_charge_id=payment.telegram_payment_charge_id
            )
            keyboard = [[InlineKeyboardButton("Buy flowers again 🌸", callback_data="get_flowers_again")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            refund_msg = random.choice(REFUND_MESSAGES)

            if update.message.chat.type == "private":
                await send_effect(update.message.chat.id, refund_msg, reply_markup)
            else:
                await update.message.reply_text(refund_msg, reply_markup=reply_markup)
            log_action("INFO", "✅ Refund completed successfully", user_info)
        except Exception as e:
            log_action("ERROR", f"❌ Error refunding payment: {e}", user_info)
            await update.message.reply_text("❌ Sorry, there was an issue processing your refund. Please contact support.")
    else:
        log_action("INFO", f"✅ Processing payment of {amount} stars (no refund)", user_info)
        await asyncio.sleep(4)
        sticker_id = random.choice(PAYMENT_STICKERS)
        await context.bot.send_sticker(chat_id=update.message.chat.id, sticker=sticker_id)
        await asyncio.sleep(4)
        keyboard = [[InlineKeyboardButton("Buy flowers again 🌸", callback_data="get_flowers_again")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        success_msg = random.choice(THANK_YOU_MESSAGES)

        if update.message.chat.type == "private":
            await send_effect(update.message.chat.id, success_msg, reply_markup)
        else:
            await update.message.reply_text(success_msg, reply_markup=reply_markup)
        log_action("INFO", "✅ Payment processed successfully", user_info)