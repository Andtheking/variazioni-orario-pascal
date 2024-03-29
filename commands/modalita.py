from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from .doAlways import doAlways
from utils.db import queryGetSingleValue, queryNoReturn


async def modalita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass