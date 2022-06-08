from datetime import datetime
from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
import pytz

updater = Updater("YOUR_TOKEN",
                  use_context=True)
  
chats = {}

def getOrCreateUsers(id):
    if id not in chats:
        chats[id] = {}
    return chats[id]

def updateUsers(id, newusers):
    chats[id] = newusers

def saveChats():
    import json
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(chats, f, ensure_ascii=False, indent=4)


def loadChats():
    import json
    import os
    if os.path.exists("data.json"):
        with open('data.json') as f:
            raw_data = json.load(f)
            for chat_id in raw_data:
                users = {}
                for user in raw_data[chat_id]:
                    users[user] = raw_data[chat_id][user]
                chats[int(chat_id)] = users
    
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Some start message")

# parts are devided by space
# note - partsum always includes command as group(1), so example:
# parseMessage("/command arg1 arg2", 3) = ("/command", "arg1", "arg2")
def parseMessage(message, partsnum):
    import re
    pattern = '(.*) ' * partsnum
    pattern = pattern[:-1]
    expresses=re.search(pattern, message)
    return expresses.groups()
    

def setMyTimezone(update: Update, context: CallbackContext):
    import datetime
    users = getOrCreateUsers(update.message.chat.id)
    text = update.message.text.strip()
    user = update.message.from_user['username']
    command, timezone = parseMessage(text, 2)
    users[user] = timezone
    users = {key: value for key, value in sorted(users.items(), key=lambda item: pytz.timezone(item[1]).utcoffset(datetime.datetime.today()).total_seconds())}
    updateUsers(update.message.chat.id, users)
    update.message.reply_text("Added {} with timezone {}".format(user, timezone))
    saveChats()

def setUserTimezone(update: Update, context: CallbackContext):
    import datetime
    users = getOrCreateUsers(update.message.chat.id)
    text = update.message.text.strip()
    command, user, timezone = parseMessage(text, 3)
    users[user] = timezone
    users = {key: value for key, value in sorted(users.items(), key=lambda item: pytz.timezone(item[1]).utcoffset(datetime.datetime.today()).total_seconds())}
    updateUsers(update.message.chat.id, users)
    update.message.reply_text("Updated {}'s timezone to {}".format(user, timezone))
    saveChats()


def show(update: Update, context: CallbackContext):
    print(chats)
    users = getOrCreateUsers(update.message.chat.id)
    print(users)
    if not users:
        update.message.reply_text("No added users yet.")
        return

    text = update.message.text.strip()
    answer = ""
    if ' ' in text:
        command, user = parseMessage(text, 2)
        answer = "{} {}".format(user, users[user])
    else:
        for user, timezone in users.items():
            answer += user + ' ' + timezone + '\n'
        answer = answer[:-1]

    update.message.reply_text(answer)
    
def remove(update: Update, context: CallbackContext):
    users = getOrCreateUsers(update.message.chat.id)
    text = update.message.text.strip()
    command, user = parseMessage(text, 2)
    if user in users:
        users.pop(user)
        update.message.reply_text("Removed user {}".format(user))
    else:
        update.message.reply_text("Couldn't find user {}".format(user))
    saveChats()
    
def expandTime(update: Update, context: CallbackContext):
    users = getOrCreateUsers(update.message.chat.id)
    user = update.message.from_user['username']
    text = update.message.text.strip()
    timezone = pytz.timezone(users[user])
    time = str(datetime.now(timezone).hour) + ":" + str(datetime.now(timezone).minute)
    if ' ' in text:
        command, time = parseMessage(text, 2)
    from dateutil.parser import parse
    from dateutil.tz import tzoffset
    requested_dt = pytz.timezone(users[user]).localize(parse(time))
    answer = ""
    for user, timezone in users.items():
        datetime_user = requested_dt.astimezone(pytz.timezone(timezone))
        answer += '@' + user + '\t' + datetime_user.strftime('%H:%M') + '\n'
    answer = answer[:-1]
    update.message.reply_text(answer)

def help(update: Update, context: CallbackContext):
    update.message.reply_text('''/start - to start the bot.
/help - to see this message.
/setMyTZ <timezone> - to update your timezone.
/setTZ <user> <timezone> - to update somebody's timezone.
/show - to see all users timezones.
/show <user> - to see user's timezone.
/remove <user> - to remove user from base.
/expand - to print current time of all in their timezone
/expand <time in your timezone> - to print message to everybody in their timezone''')

def unknown(update: Update, context: CallbackContext):
    update.message.reply_text("Sorry, {} is not a valid command".format(update.message.text))

updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('help', help))
updater.dispatcher.add_handler(CommandHandler('setMyTZ', setMyTimezone))
updater.dispatcher.add_handler(CommandHandler('setTZ', setUserTimezone))
updater.dispatcher.add_handler(CommandHandler('show', show))
updater.dispatcher.add_handler(CommandHandler('remove', remove))
updater.dispatcher.add_handler(CommandHandler('expand', expandTime))



updater.dispatcher.add_handler(MessageHandler(Filters.text, unknown))
updater.dispatcher.add_handler(MessageHandler(
    # Filters out unknown commands
    Filters.command, unknown))

loadChats()
updater.start_polling()