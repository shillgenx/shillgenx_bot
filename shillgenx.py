from telebot.async_telebot import AsyncTeleBot
from telebot import types
from dotenv import load_dotenv
from pymongo import MongoClient
import os
import asyncio

from db.schemas import Project, ShillgenXTarget

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = AsyncTeleBot(TELEGRAM_BOT_TOKEN)

MONGO_USERNAME = os.getenv('MONGO_USERNAME')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')
MONGO_HOST = os.getenv('MONGO_HOST')
MONGO_PORT = os.getenv('MONGO_PORT')
MONGO_DB = os.getenv('MONGO_DB')
conn_str = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}"
client = MongoClient(conn_str)
db = client[MONGO_DB]

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Dictionary to store the state and data for each chat
chat_states = {}

# Define states
AWAITING_COMMAND, AWAITING_PROJECT_NAME, AWAITING_PROJECT_DESCRIPTION, AWAITING_WEBSITE, AWAITING_X_HANDLE, AWAITING_TAGS = range(0, 6)
AWAITING_X_TARGET_LINK, AWAITING_LOCK_DURATION= range(6, 8)
AWAITING_ITEM_TO_EDIT, AWAITING_NEW_VALUE = range(8, 10)
GENERATING_POST = range(10, 10)

#################################################################
#                                                               #
#                   SHILLGENX DB OPERATIONS                     #
#                                                               #
#################################################################
def db_add_project(project: Project):
    collection = db.users
    result = collection.insert_one({"name": "Alice", "age": 30})
    print(result)

def db_get_project(telegram_chat_id: str):
    collection = db.users
    user = collection.find_one({"name": "Alice"})
    print(user)

def is_permission_granted():
    return True

@bot.message_handler(commands=['shillgenx'])
async def handle_shillgenx(message):
    db_add_project(project=None)
    db_get_project(telegram_chat_id=None)
    chat_id = message.chat.id
    chat_states[chat_id] = {'state': AWAITING_PROJECT_NAME}
    await bot.send_message(chat_id, "What is the name of your project?")

@bot.message_handler(func=lambda message: chat_states.get(message.chat.id, {}).get('state') == AWAITING_PROJECT_NAME)
async def process_project_name(message):
    chat_id = message.chat.id
    chat_states[chat_id]['project_name'] = message.text
    chat_states[chat_id]['state'] = AWAITING_PROJECT_DESCRIPTION
    await bot.send_message(chat_id, "Tell me about your project! You can include details about the following (the more I know, the better):\nProduct\nTechnology\nSecurity\nNarrative\nRoadmap\nUse Case\nCommunity\n")

@bot.message_handler(func=lambda message: chat_states.get(message.chat.id, {}).get('state') == AWAITING_PROJECT_DESCRIPTION)
async def process_x_handle(message):
    chat_id = message.chat.id
    chat_states[chat_id]['x_handle'] = message.text
    chat_states[chat_id]['state'] = AWAITING_WEBSITE
    await bot.send_message(chat_id, "What is the X Handle of your project? (@example)")

@bot.message_handler(func=lambda message: chat_states.get(message.chat.id, {}).get('state') == AWAITING_WEBSITE)
async def process_website(message):
    chat_id = message.chat.id
    chat_states[chat_id]['website'] = message.text
    chat_states[chat_id]['state'] = AWAITING_TAGS
    await bot.send_message(chat_id, "What are some tags for your project? ($EXAMPLE, #EXAMPLE)")

@bot.message_handler(func=lambda message: chat_states.get(message.chat.id, {}).get('state') == AWAITING_TAGS)
async def process_tags(message):
    chat_id = message.chat.id
    chat_states[chat_id]['tags'] = message.text
    del chat_states[chat_id]
    await bot.send_message(chat_id, "Thank you! Now use /shillx to start raiding!")

@bot.message_handler(commands=['shillx'])
async def process_shillx(message):
    chat_id = message.chat.id
    if is_permission_granted():
        try:
            # Restricting all members from sending messages
            permissions = types.ChatPermissions(can_send_messages=False)
            await bot.set_chat_permissions(chat_id, permissions)
            print("Chat locked")
        except Exception as e:
            print("An error occurred:", e)

    chat_states[chat_id] = {'state': AWAITING_X_TARGET_LINK}
    await bot.send_message(chat_id, "Paste the link to raid target!")

@bot.message_handler(func=lambda message: chat_states.get(message.chat.id, {}).get('state') == AWAITING_X_TARGET_LINK)
async def process_x_target_link(message):
    chat_id = message.chat.id
    chat_states[chat_id]['x_target_link_id'] = "mongodbid"
    chat_states[chat_id]['x_target_link'] = message.text
    chat_states[chat_id]['state'] = AWAITING_LOCK_DURATION
    if is_permission_granted():
        await bot.delete_message(chat_id, message.message_id)
    await bot.send_message(chat_id, f"How many minutes to lock chat for?")

@bot.message_handler(func=lambda message: chat_states.get(message.chat.id, {}).get('state') == AWAITING_LOCK_DURATION)
async def process_duration(message):
    chat_id = message.chat.id
    chat_states[chat_id]['duration'] = int(message.text)
    await bot.send_message(chat_id, f"https://t.me/shillgenx_test_bot?start={chat_id}_{chat_states[chat_id]['x_target_link_id']}")

    if is_permission_granted():
        try:
            # # Restricting all members from sending messages
            # permissions = types.ChatPermissions(can_send_messages=False)
            # await bot.set_chat_permissions(chat_id, permissions)
            await bot.send_message(chat_id, f"Chat is locked for {int(message.text)} minute(s).")

            await asyncio.sleep(int(message.text) * 60)

            # Reverting permissions to allow sending messages
            permissions = types.ChatPermissions(can_send_messages=True)
            await bot.set_chat_permissions(chat_id, permissions)
            await bot.send_message(chat_id, "Chat is unlocked now.")
        except Exception as e:
            print("An error occurred:", e)
    del chat_states[chat_id]

@bot.message_handler(commands=['start'])
async def handle_start(message):
    args = message.text.split(maxsplit=1)
    print(args)
    if len(args) > 1:
        params = args[1].split('_')
        await bot.send_message(message.chat.id, f"Received parameters: {params}")
    else:
        await bot.send_message(message.chat.id, "Welcome to the bot!")

async def run_bot():
    await bot.polling()

if __name__ == '__main__':
    asyncio.run(run_bot())
