"""Async handlers for the Mira Telegram bot (python-telegram-bot v20)."""

from __future__ import annotations

import sqlite3
from typing import Dict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)

from bot.keyboards import (
    segment_keyboard,
    main_menu_keyboard,
    after_task_keyboard,
    back_to_menu_keyboard,
)
from backend import services
from backend.database import get_connection

# Conversation states
SEGMENT, MAIN_MENU, AWAITING_PROOF = range(3)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    args = context.args or []
    referral = args[0] if args else None

    user = update.effective_user
    telegram_id = user.id
    username = user.username or user.full_name

    # register or fetch existing
    u = services.register_user(
        telegram_id=telegram_id, username=username, segment=None, referral_code=referral
    )
    # store basic info
    context.user_data["user"] = u

    if not u.get("segment"):
        await update.effective_message.reply_text(
            "Welcome to Mira Loop! 🚀\nWho are you?", reply_markup=segment_keyboard()
        )
        return SEGMENT

    await update.effective_message.reply_text(
        f"Welcome back, {u['username']}! ⭐ XP: {u['xp']}",
        reply_markup=main_menu_keyboard(),
    )
    return MAIN_MENU


async def segment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data  # e.g. 'segment_student'
    segment = data.split("_", 1)[1]

    telegram_id = update.effective_user.id

    # update user's segment in DB
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET segment = ? WHERE telegram_id = ?", (segment, telegram_id)
        )
        conn.commit()
        # fetch user id
        cur.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
        user_id = row[0] if row else None
    finally:
        conn.close()

    # check if user came via referral
    bonus_sent = False
    if user_id:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM referrals WHERE referred_id = ?", (user_id,))
            if cur.fetchone():
                await query.message.reply_text("🎉 Bonus! +30 XP added")
                bonus_sent = True
        finally:
            conn.close()

    await query.message.reply_text(
        f"Great! You're set as {segment}. Let's go! 💪",
        reply_markup=main_menu_keyboard(),
    )
    return MAIN_MENU


async def get_task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    telegram_id = update.effective_user.id

    # get user id
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
        if not row:
            await query.message.reply_text("User not registered. Use /start")
            return SEGMENT
        user_id = row[0]
    finally:
        conn.close()

    task = services.get_next_task(user_id)
    if not task:
        await query.message.reply_text("No tasks available right now.")
        return MAIN_MENU

    context.user_data["current_task"] = task

    await query.message.reply_text(task["text"], parse_mode="Markdown")
    if task["proof_type"] == "screenshot":
        await query.message.reply_text("📸 Send a screenshot of your result")
    else:
        await query.message.reply_text("✍️ Paste your answer here (min 50 chars)")

    return AWAITING_PROOF


async def proof_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = update.message
    user = update.effective_user
    telegram_id = user.id

    task = context.user_data.get("current_task")
    if not task:
        await msg.reply_text(
            "No active task. Choose one from the menu.",
            reply_markup=main_menu_keyboard(),
        )
        return MAIN_MENU

    if msg.photo:
        proof_type = "screenshot"
        proof_content = msg.photo[-1].file_id
    elif msg.text:
        proof_type = "text"
        proof_content = msg.text
    else:
        await msg.reply_text("❌ Please send a screenshot or text answer")
        return AWAITING_PROOF

    # get user id
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
        if not row:
            await msg.reply_text("User not found. Use /start")
            return SEGMENT
        user_id = row[0]
    finally:
        conn.close()

    result = services.submit_proof(user_id, task["task_id"], proof_type, proof_content)

    if not result.get("approved"):
        await msg.reply_text(f"❌ {result.get('reason')}. Try again.")
        return AWAITING_PROOF

    await msg.reply_text(
        f"✅ Done! +{result.get('xp_earned')} XP\n🏅 Rank: #{result.get('rank')}\n⭐ Total XP: {result.get('total_xp')}",
        reply_markup=after_task_keyboard(),
    )

    # notify referrer if any
    referrer = result.get("referrer_telegram_id")
    if referrer:
        try:
            await context.bot.send_message(
                referrer,
                "🎉 Your friend just completed a challenge! +50 XP added to your score 🚀",
            )
        except Exception:
            pass

    # clear current task
    context.user_data.pop("current_task", None)
    return MAIN_MENU


async def leaderboard_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()
    rows = services.get_leaderboard()
    text = "🏆 Top 10\n\n"
    for r in rows:
        text += f"{r['rank']}. {r['username']} ({r['segment']}) — {r['xp']} XP\n"
    await query.message.reply_text(text, reply_markup=back_to_menu_keyboard())


async def invite_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    telegram_id = update.effective_user.id
    link = services.get_referral_link(telegram_id)
    profile = services.get_user_profile(telegram_id)
    referred = profile.get("referred_count") if profile else 0

    text = f"🔗 Your referral link:\n{link}\n\n👥 Friends invited: {referred}\n"
    kb = (
        InlineKeyboardMarkup([[InlineKeyboardButton("Share link", url=link)]])
        if link
        else None
    )
    await query.message.reply_text(text, reply_markup=kb or back_to_menu_keyboard())


async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    telegram_id = update.effective_user.id
    profile = services.get_user_profile(telegram_id)
    if not profile:
        await query.message.reply_text("Profile not found. Use /start")
        return

    text = (
        f"👤 {profile['username']}\n"
        f"🎯 {profile['segment']}\n"
        f"⭐ XP: {profile['xp']}\n"
        f"🏅 Rank: #{profile['rank']}\n"
        f"✅ Tasks done: {profile['tasks_completed']}\n"
        f"👥 Friends invited: {profile['referred_count']}"
    )
    await query.message.reply_text(text, reply_markup=back_to_menu_keyboard())


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # This handler is used for explicit 'main_menu' callbacks
    query = update.callback_query
    if query:
        await query.answer()
        await query.message.reply_text("Main Menu", reply_markup=main_menu_keyboard())
    else:
        await update.effective_message.reply_text(
            "Main Menu", reply_markup=main_menu_keyboard()
        )
    return MAIN_MENU


def get_conversation_handler() -> ConversationHandler:
    """Construct and return a ConversationHandler instance."""
    return ConversationHandler(
        entry_points=[CommandHandler("start", start_handler)],
        states={
            SEGMENT: [CallbackQueryHandler(segment_handler, pattern=r"^segment_")],
            MAIN_MENU: [
                CallbackQueryHandler(get_task_handler, pattern=r"^get_task$"),
                CallbackQueryHandler(leaderboard_handler, pattern=r"^leaderboard$"),
                CallbackQueryHandler(invite_handler, pattern=r"^invite$"),
                CallbackQueryHandler(profile_handler, pattern=r"^profile$"),
                CallbackQueryHandler(main_menu_handler, pattern=r"^main_menu$"),
            ],
            AWAITING_PROOF: [
                MessageHandler(
                    filters.PHOTO | (filters.TEXT & ~filters.COMMAND), proof_handler
                ),
                CallbackQueryHandler(main_menu_handler, pattern=r"^main_menu$"),
            ],
        },
        fallbacks=[CommandHandler("start", start_handler)],
    )


__all__ = ["get_conversation_handler", "SEGMENT", "MAIN_MENU", "AWAITING_PROOF"]
