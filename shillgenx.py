from telebot.async_telebot import AsyncTeleBot
from telebot import types
from dotenv import load_dotenv
from pymongo import MongoClient
from bson.objectid import ObjectId
from dataclasses import asdict
from typing import List, Dict
import os
import asyncio

from db.schemas import Project, ShillgenXTarget, Schemas

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
    try:
        project_dict = asdict(project)
        del project_dict['_id']
        
        if db_get_project(project_dict["group_chat_id"]):
            raise Exception("A project for this group chat already exists.")

        collection = db["project"]
        result = collection.insert_one(project_dict)
        new_project_id = result.inserted_id
        new_project = collection.find_one({'_id': new_project_id})
    except Exception as e:
        print(f"An error occured: {e}")

    return new_project

def db_get_project(telegram_chat_id: str) -> Dict:
    try:
        collection = db["project"]
        project = collection.find_one({"group_chat_id": telegram_chat_id})
    except Exception as e:
        print(f"An error occured: {e}")
    return project

def db_delete_project(telegram_chat_id: str) -> bool:
    try:
        collection = db["project"]
        result = collection.delete_one({"group_chat_id": telegram_chat_id})
        if result.deleted_count > 0:
            return True
    except Exception as e:
        print(f"An error occured: {e}")
    return False

def db_edit_project(group_chat_id: str, field: str, new_value: str):
    try:
        query = {"group_chat_id": group_chat_id}
        updates = {"$set": {field: new_value}}

        collection = db["project"]
        result = collection.update_one(query, updates)
        return result
    except Exception as e:
        print(f"An error occured: {e}")

def db_add_target(target: ShillgenXTarget):
    try:
        target_dict = asdict(target)
        del target_dict['_id']

        collection = db["target"]
        result = collection.insert_one(target_dict)
        new_target_id = result.inserted_id
        new_target = collection.find_one({'_id': new_target_id})
    except Exception as e:
        print(f"An error occured: {e}")

    return new_target

def db_get_target(object_id: str) -> Dict:
    try:
        collection = db["target"]
        object_id = ObjectId(object_id)
        target = collection.find_one({"_id": object_id})
    except Exception as e:
        print(f"An error occured: {e}")
    return target

#################################################################
#                                                               #
#                       TEST FUNCTIONS                          #
#                                                               #
#################################################################
MONGODB_COLLECTIONS = [schema.name for schema in Schemas]
@bot.message_handler(commands=['dropcollections'])
async def handle_drop_collection(message):
    for c in MONGODB_COLLECTIONS:
        collection = db[c]
        collection.drop()
    await bot.send_message(message.chat.id, "Collections dropped.")


#################################################################
#                                                               #
#                      HELPER FUNCTIONS                         #
#                                                               #
#################################################################
async def is_user_admin(chat_id, user_id):
    try:
        chat_administrators = await bot.get_chat_administrators(chat_id)
        return any(admin.user.id == user_id for admin in chat_administrators)
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False

def is_permission_granted():
    return True

#################################################################
#                                                               #
#                      BOT FLOW FUNCTIONS                       #
#                                                               #
#################################################################

@bot.message_handler(commands=['cancel'])
async def handle_cancel(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not chat_states[chat_id]['current_user'] == user_id:
        return

    del chat_states[chat_id]
    await bot.send_message(chat_id, "Operation canceled.")

@bot.message_handler(commands=['sgx_setup'])
async def handle_shillgenx_setup(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not await is_user_admin(chat_id, user_id):
        await bot.reply_to(message, "You must be an admin for this operation.")
        return

    if db_get_project(chat_id):
        await bot.send_message(chat_id, "A ShillgenX account is already setup in this chat. Use /sgx_delete to start over.")
        return

    chat_states[chat_id] = {
        'state': AWAITING_PROJECT_NAME,
        'current_user': user_id,
        'project': Project()
        }
    await bot.send_message(chat_id, "What is the name of your project?")

@bot.message_handler(commands=['sgx_delete'])
async def handle_shillgenx_delete(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not await is_user_admin(chat_id, user_id):
        await bot.reply_to(message, "You must be an admin for this operation.")

    if db_delete_project(chat_id):
        await bot.send_message(chat_id, "ShillgenX account successfully deleted.")
        return
    await bot.send_message(chat_id, "Something went wrong.")

@bot.message_handler(func=lambda message: chat_states.get(message.chat.id, {}).get('state') == AWAITING_PROJECT_NAME)
async def process_project_name(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if chat_states[chat_id]['current_user'] and not chat_states[chat_id]['current_user'] == user_id:
        return

    try:
        chat_states[chat_id]['project'].set_name(message.text)
        chat_states[chat_id]['project_name'] = message.text
        chat_states[chat_id]['state'] = AWAITING_PROJECT_DESCRIPTION
        await bot.send_message(chat_id, "Tell me about your project! You can include details about the following (the more I know, the better):\nProduct\nTechnology\nSecurity\nNarrative\nRoadmap\nUse Case\nCommunity\n")
    except ValueError as e:
        await bot.send_message(chat_id, f"{e}")
    except Exception as e:
        print(f"An error occured: {e}")

@bot.message_handler(func=lambda message: chat_states.get(message.chat.id, {}).get('state') == AWAITING_PROJECT_DESCRIPTION)
async def process_project_description(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if chat_states[chat_id]['current_user'] and not chat_states[chat_id]['current_user'] == user_id:
        return

    try:
        chat_states[chat_id]['project'].set_description(message.text)
        chat_states[chat_id]['project_description'] = message.text
        chat_states[chat_id]['state'] = AWAITING_X_HANDLE
        await bot.send_message(chat_id, "What is the X Handle of your project?\nExample:\n@example")
    except ValueError as e:
        await bot.send_message(chat_id, f"{e}")
    except Exception as e:
        print(f"An error occured: {e}")

@bot.message_handler(func=lambda message: chat_states.get(message.chat.id, {}).get('state') == AWAITING_X_HANDLE)
async def process_x_handle(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if chat_states[chat_id]['current_user'] and not chat_states[chat_id]['current_user'] == user_id:
        return
    try:
        chat_states[chat_id]['project'].set_x_handle(message.text)
        chat_states[chat_id]['x_handle'] = message.text
        chat_states[chat_id]['state'] = AWAITING_WEBSITE
        await bot.send_message(chat_id, "What is your project's website?\nExample:\nwww.example.ai")
    except ValueError as e:
        await bot.send_message(chat_id, f"{e}")
    except Exception as e:
        print(f"An error occured: {e}")

@bot.message_handler(func=lambda message: chat_states.get(message.chat.id, {}).get('state') == AWAITING_WEBSITE)
async def process_website(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if chat_states[chat_id]['current_user'] and not chat_states[chat_id]['current_user'] == user_id:
        return

    try:
        chat_states[chat_id]['project'].set_website(message.text)
        chat_states[chat_id]['website'] = message.text
        chat_states[chat_id]['state'] = AWAITING_TAGS
        await bot.send_message(chat_id, "What are some tags for your project?\nExample:\n$EXAMPLE, #EXAMPLE")
    except ValueError as e:
        await bot.send_message(chat_id, f"{e}")
    except Exception as e:
        print(f"An error occured: {e}")

@bot.message_handler(func=lambda message: chat_states.get(message.chat.id, {}).get('state') == AWAITING_TAGS)
async def process_tags(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if chat_states[chat_id]['current_user'] and not chat_states[chat_id]['current_user'] == user_id:
        return

    # Get the telegram group invite link
    try:
        invite_link = await bot.export_chat_invite_link(chat_id)
    except Exception as e:
        print(f"An error occured: {e}")

    try:
        chat_states[chat_id]['project'].set_tags_string(message.text)
        chat_states[chat_id]['tags'] = message.text

        chat_states[chat_id]['project'].set_group_chat_id(chat_id)
        chat_states[chat_id]['project'].set_telegram(invite_link)
        created_project = db_add_project(chat_states[chat_id]['project'])

        print(chat_states[chat_id]['project'])

        del chat_states[chat_id]
        await bot.send_message(chat_id, "Thank you! Now use /shillx to start raiding!")
    except ValueError as e:
        await bot.send_message(chat_id, f"{e}")
    except Exception as e:
        print(f"An error occured: {e}")

@bot.message_handler(commands=['shillx'])
async def process_shillx(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if is_permission_granted():
        try:
            # Restricting all members from sending messages
            permissions = types.ChatPermissions(can_send_messages=False)
            await bot.set_chat_permissions(chat_id, permissions)
            print("Chat locked")
        except Exception as e:
            print("An error occurred:", e)

    chat_states[chat_id] = {
        'state': AWAITING_X_TARGET_LINK,
        'current_user': user_id}
    await bot.send_message(chat_id, "Paste the link to raid target!")

@bot.message_handler(func=lambda message: chat_states.get(message.chat.id, {}).get('state') == AWAITING_X_TARGET_LINK)
async def process_x_target_link(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not chat_states[chat_id]['current_user'] == user_id:
        return

    chat_states[chat_id]['x_target_link_id'] = "mongodbid"
    chat_states[chat_id]['x_target_link'] = message.text
    chat_states[chat_id]['state'] = AWAITING_LOCK_DURATION
    if is_permission_granted():
        await bot.delete_message(chat_id, message.message_id)
    await bot.send_message(chat_id, f"How many minutes to lock chat for?")

@bot.message_handler(func=lambda message: chat_states.get(message.chat.id, {}).get('state') == AWAITING_LOCK_DURATION)
async def process_duration(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not chat_states[chat_id]['current_user'] == user_id:
        return

    try:
        project = db_get_project(chat_id)

        target = {
            "_id": '',
            "project_id": project['_id'],
            "group_chat_id": chat_id,
            "x_target_link": chat_states[chat_id]['x_target_link'],
            "lock_duration": int(message.text)
        }

        target = ShillgenXTarget(**target)
        created_target = db_add_target(target)

        await bot.send_message(chat_id, f"https://t.me/shillgenx_test_bot?start={created_target['group_chat_id']}_{created_target['_id']}")

        if is_permission_granted():
            # # Restricting all members from sending messages
            # permissions = types.ChatPermissions(can_send_messages=False)
            # await bot.set_chat_permissions(chat_id, permissions)
            await bot.send_message(chat_id, f"Chat is locked for {created_target['lock_duration']} minute(s).")

            await asyncio.sleep(created_target['lock_duration'] * 60)

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
    if len(args) > 1:
        params = args[1].split('_')
        group_chat_id = params[0]
        shill_target_id = params[1]
        target_object = db_get_target(shill_target_id)
        project_object = db_get_project(target_object["group_chat_id"])
        await bot.send_message(message.chat.id, f"Target Details: {target_object}\nProject Details: {project_object}")
    else:
        await bot.send_message(message.chat.id, "Welcome to the bot!")

async def run_bot():
    await bot.polling()

if __name__ == '__main__':
    asyncio.run(run_bot())
