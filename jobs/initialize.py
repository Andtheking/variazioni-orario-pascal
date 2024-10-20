from telegram.ext import ContextTypes
from utils.log import log
from utils.regex_image import get_regex_image
from requirements import config



async def initialize(context: ContextTypes.DEFAULT_TYPE):
    log("Bot online at: https://t.me/" + context.bot.username)
    