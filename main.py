from functools import wraps
import re
import os
import shutil
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    MessageHandler,
    filters
)
import yaml
from yaml.loader import SafeLoader
import requests
import logging
import logging.config
import time

logging.config.fileConfig(fname='logger.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)

logging.getLogger('httpx').setLevel(logging.WARNING)

LIST_OF_ID = []
LIST_OF_USERNAMES = []
SHUTDOWN_SCHEDULED = False

def send_message(chat_id, message):
    requests.post(
        url='https://api.telegram.org/bot{0}/sendMessage'.format(TOKEN),
        data={'chat_id': chat_id, 'text': message}
    )

def notify_to_ids(message):
    for chat_id in NOTIFY_ID:
        send_message(chat_id, message)
        
def restricted(func):
    @wraps(func)
    async def wrapped(update, context, *args, **kwargs):
        user = update.message.from_user
        if user['id'] not in LIST_OF_ID and user['username'] not in LIST_OF_USERNAMES:
            logger.warning("Unauthorized access attempt by {} with user ID: {}".format(
                user['username'], user['id']))
            print(user)
            await update.message.reply_text(
                "You are not authorized to use this bot. Please contact the administrator."
            )
            logger.critical("Unauthorized access denied for {} and his user ID: {} ".format(
                user['username'], user['id']))
            return
        print(user)
        return await func(update, context, *args, **kwargs)
    return wrapped

@restricted
async def help(update: Update, _: CallbackContext):
    await update.message.reply_text('Commands: Off, Abort')

@restricted
async def power_off(update: Update, _):
    global SHUTDOWN_SCHEDULED
    if SHUTDOWN_SCHEDULED:
        await update.message.reply_text('Shutdown already scheduled')
        return
    await update.message.reply_text('Shutdown scheduled')
    logger.info("Shutdown scheduled by user: {} with ID: {}".format(
        update.message.from_user.username, update.message.from_user.id))
    SHUTDOWN_SCHEDULED = True
    os.system('shutdown +5')

@restricted
async def power_off_abort(update: Update, _):
    global SHUTDOWN_SCHEDULED
    await update.message.reply_text('Shutdown aborted')
    logger.info("Shutdown aborted by user: {} with ID: {}".format(
        update.message.from_user.username, update.message.from_user.id))
    os.system('shutdown -c')
    SHUTDOWN_SCHEDULED = False

def main():
    # notify_to_ids(f'{HOST} powered on')
    app = Application.builder().token(TOKEN).read_timeout(120).write_timeout(120).build()
    help_regex = "(^(h|H)elp$)"
    poweroff_regex = "(^(o|O)ff$)"
    poweroff_regex_abort = "(^(a|A)bort$)"

    app.add_handler(CommandHandler("start", help))

    app.add_handler(MessageHandler(filters.Regex(help_regex), help))
    app.add_handler(MessageHandler(filters.Regex(poweroff_regex), power_off))
    app.add_handler(MessageHandler(filters.Regex(poweroff_regex_abort), power_off_abort))

    app.run_polling()


if __name__ == "__main__":
    # Load config file
    abs_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(abs_path, 'config.yml'), 'r') as f:
        config = yaml.load(f, SafeLoader)

    TOKEN = config['telegram']['token']
    ADMIN_ID = config['telegram']['admin_id']
    LIST_OF_ID = config['telegram']['whitelist_users'].values()
    LIST_OF_USERNAMES = config['telegram']['whitelist_users'].keys()
    NOTIFY_ID = config['telegram']['notify_ids']
    START_TIME = time.time()
    
    logger.info("Started Arch Bot at {}".format(
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(START_TIME))))

    notify_to_ids(f"Arch turned on") 
    main()