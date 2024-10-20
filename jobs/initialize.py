from telegram.ext import ContextTypes
from utils.log import log

async def initialize(context: ContextTypes.DEFAULT_TYPE):
    log("Bot online at: https://t.me/" + context.bot.username)
    