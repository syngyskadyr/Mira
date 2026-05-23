"""Keyboard definitions for the bot using python-telegram-bot v20.

Provides helper functions that return `InlineKeyboardMarkup` instances used
throughout the bot.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def segment_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for choosing a user segment (student/marketer/founder)."""
    keyboard = [
        [
            InlineKeyboardButton("🎓 Student", callback_data="segment_student"),
            InlineKeyboardButton("📣 Marketer", callback_data="segment_marketer"),
            InlineKeyboardButton("🚀 Founder", callback_data="segment_founder"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu keyboard (2x2 grid)."""
    keyboard = [
        [
            InlineKeyboardButton("🎯 Get Challenge", callback_data="get_task"),
            InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard"),
        ],
        [
            InlineKeyboardButton("🔗 Invite Friend", callback_data="invite"),
            InlineKeyboardButton("👤 My Profile", callback_data="profile"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def after_task_keyboard() -> InlineKeyboardMarkup:
    """Keyboard shown after completing or viewing a task."""
    keyboard = [
        [
            InlineKeyboardButton("🎯 Next Challenge", callback_data="get_task"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Single-button keyboard to return to main menu."""
    keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)


__all__ = [
    "segment_keyboard",
    "main_menu_keyboard",
    "after_task_keyboard",
    "back_to_menu_keyboard",
]
