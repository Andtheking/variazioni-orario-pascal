TOKEN = '5264178692:AAG2aN936LktECE_GtEgmzONAq8Yvmpb4W4'

import logging
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

from sito import *
import os
import requests

PORT = int(os.environ.get('PORT','8443'))
CLASSE = 0

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def help(update, context):
    logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    update.message.reply_text("Ecco l'help")

def start(update,context):
    logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    update.message.reply_text("Primissima versione del bot (fa cagare per ora): scrivi /impostaClasse <CLASSE_MAIUSCOLA>")

def impostaClasse(update, context):
    logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    update.message.reply_text("Mandami la classe nel formato \"1A\" oppure annulla con /cancel")
    return CLASSE



def ClasseImpostata(update, context):
    logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha impostato \"{update.message.text}\" come classe alle {update.message.date}")
    update.message.reply_text("Classe impostata. (in realtà ancora no. ci sto lavorando per cui ora mando la variazione")
    update.message.reply_text(Main(update.message.text))
    return ConversationHandler.END
    

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
def cancel(update, context):
    update.message.reply_text("Azione annullata.")
    return ConversationHandler.END
    
    
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    requests.post('https://api.telegram.org/bot5264178692:AAG2aN936LktECE_GtEgmzONAq8Yvmpb4W4/sendMessage?chat_id=245996916&text=Bot%20online!')
     
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
     
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("impostaClasse", impostaClasse)],
        states={
            CLASSE: [MessageHandler(Filters.text & ~ Filters.command, ClasseImpostata)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    dp.add_handler(conversation_handler)
    
    dp.add_error_handler(error)
    
    updater.start_webhook(listen="0.0.0.0", port=int(PORT), url_path=TOKEN, webhook_url="https://variazioni-orario-pascal.herokuapp.com/" + TOKEN)
    updater.idle()

if __name__ == '__main__':
    main()
