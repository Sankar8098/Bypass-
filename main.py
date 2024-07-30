from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand,
    Message,
)
from os import environ, remove
from threading import Thread
from json import load
from re import search

from texts import HELP_TEXT
import bypasser
import freewall
from time import time
from db import DB

# bot
with open("config.json", "r") as f:
    DATA = load(f)

def getenv(var):
    return environ.get(var) or DATA.get(var, None)

bot_token = getenv("bot_token")
api_hash = getenv("api_hash")
api_id = getenv("api_id")

# Print loaded values for debugging
print(f"bot_token: {bot_token}")
print(f"api_hash: {api_hash}")
print(f"api_id: {api_id}")

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

with app:
    app.set_bot_commands(
        [
            BotCommand("start", "Welcome Message"),
            BotCommand("help", "List of All Supported Sites"),
        ]
    )

# DB
db_api = getenv("DB_API")
db_owner = getenv("DB_OWNER")
db_name = getenv("DB_NAME")
try:
    database = DB(api_key=db_api, db_owner=db_owner, db_name=db_name)
except: 
    print("Database is Not Set")
    database = None

# handle index
def handleIndex(ele: str, message: Message, msg: Message):
    result = bypasser.scrapeIndex(ele)
    try:
        app.delete_messages(message.chat.id, msg.id)
    except:
        pass
    if database and result: database.insert(ele, result)
    for page in result:
        app.send_message(
            message.chat.id,
            page,
            reply_to_message_id=message.id,
            disable_web_page_preview=True,
        )

# loop thread
def loopthread(message: Message, otherss=False):

    urls = []
    if otherss:
        texts = message.caption
    else:
        texts = message.text

    if texts in [None, ""]:
        return
    for ele in texts.split():
        if "http://" in ele or "https://" in ele:
            urls.append(ele)
    if len(urls) == 0:
        return

    if bypasser.ispresent(bypasser.ddl.ddllist, urls[0]):
        msg: Message = app.send_message(
            message.chat.id, "⚡ __generating...__", reply_to_message_id=message.id
        )
    elif freewall.pass_paywall(urls[0], check=True):
        msg: Message = app.send_message(
            message.chat.id, "🕴️ __jumping the wall...__", reply_to_message_id=message.id
        )
    else:
        if "https://olamovies" in urls[0] or "https://psa.wf/" in urls[0]:
            msg: Message = app.send_message(
                message.chat.id,
                "⏳ __this might take some time...__",
                reply_to_message_id=message.id,
            )
        else:
            msg: Message = app.send_message(
                message.chat.id, "🔎 __bypassing...__", reply_to_message_id=message.id
            )

    strt = time()
    links = ""
    temp = None

    for ele in urls:
        if database: df_find = database.find(ele)
        else: df_find = None
        if df_find:
            print("Found in DB")
            temp = df_find
        elif search(r"https?:\/\/(?:[\w.-]+)?\.\w+\/\d+:", ele):
            handleIndex(ele, message, msg)
            return
        elif bypasser.ispresent(bypasser.ddl.ddllist, ele):
            try:
                temp = bypasser.ddl.direct_link_generator(ele)
            except Exception as e:
                temp = "**Error**: " + str(e)
        elif freewall.pass_paywall(ele, check=True):
            freefile = freewall.pass_paywall(ele)
            if freefile:
                try:
                    app.send_document(
                        message.chat.id, freefile, reply_to_message_id=message.id
                    )
                    remove(freefile)
                    app.delete_messages(message.chat.id, [msg.id])
                    return
                except:
                    pass
            else:
                app.send_message(
                    message.chat.id, "__Failed to Jump", reply_to_message_id=message.id
                )
        else:
            try:
                temp = bypasser.shortners(ele)
            except Exception as e:
                temp = "**Error**: " + str(e)

        print("bypassed:", temp)
        if temp != None:
            if (not df_find) and ("http://" in temp or "https://" in temp) and database:
                print("Adding to DB")
                database.insert(ele, temp)
            links = links + temp + "\n"

    end = time()
    print("Took " + "{:.2f}".format(end - strt) + "sec")

    if otherss:
        try:
            app.send_photo(
                message.chat.id,
                message.photo.file_id,
                f"__{links}__",
                reply_to_message_id=message.id,
            )
            app.delete_messages(message.chat.id, [msg.id])
            return
        except:
            pass

    try:
        final = []
        tmp = ""
        for ele in links.split("\n"):
            tmp += ele + "\n"
            if len(tmp) > 4000:
                final.append(tmp)
                tmp = ""
        final.append(tmp)
        app.delete_messages(message.chat.id, msg.id)
        tmsgid = message.id
        for ele in final:
            tmsg = app.send_message(
                message.chat.id,
                f"__{ele}__",
                reply_to_message_id=tmsgid,
                disable_web_page_preview=True,
            )
            tmsgid = tmsg.id
    except Exception as e:
        app.send_message(
            message.chat.id,
            f"__Failed to Bypass : {e}__",
            reply_to_message_id=message.id,
        )

# start command
@app.on_message(filters.command(["start"]))
async def send_start(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    if str(message.chat.id).startswith("-100") and message.chat.id not in GROUP_ID:
        return
    elif message.chat.id not in GROUP_ID:
        if UPDATES_CHANNEL != "None":
            try:
                user = await app.get_chat_member(UPDATES_CHANNEL, message.chat.id)
                if user.status == enums.ChatMemberStatus.BANNED:
                    await app.send_message(
                        chat_id=message.chat.id,
                        text=f"__Sorry, you are banned. Contact My [ Owner ](https://telegram.me/{OWNER_USERNAME})__",
                        disable_web_page_preview=True
                    )
                    return
            except UserNotParticipant:
                 await app.send_message(
                    chat_id=message.chat.id,
                    text="<i>🔐 Join Channel To Use Me 🔐</i>",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("🔓 Join Now 🔓", url=f"https://t.me/{UPDATES_CHANNEL}")
                            ]
                        ]
                    ),

                )
                 return
            except Exception:
                await app.send_message(
                    chat_id=message.chat.id,
                    text=f"<i>Something went wrong</i> <b> <a href='https://telegram.me/{OWNER_USERNAME}'>CLICK HERE FOR SUPPORT </a></b>",

                    disable_web_page_preview=True)
                return
    await app.send_message(message.chat.id, f"__👋 Hi **{message.from_user.mention}**, i am Link Bypasser Bot, just send me any supported links and i will you get you results.\nCheckout /help to Read More__",
                           reply_markup=InlineKeyboardMarkup([[ InlineKeyboardButton("❤️ Owner ❤️", url=f"https://telegram.me/{OWNER_USERNAME}")]]), reply_to_message_id=message.id)


# help command
@app.on_message(filters.command(["help"]))
async def send_help(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    if str(message.chat.id).startswith("-100") and message.chat.id not in GROUP_ID:
        return
    elif message.chat.id not in GROUP_ID:
            try:
                user = await app.get_chat_member(UPDATES_CHANNEL, message.chat.id)
                if user.status == enums.ChatMemberStatus.BANNED:
                    await app.send_message(
                        chat_id=message.chat.id,
                        text=f"__Sorry, you are banned. Contact My [ Owner ](https://telegram.me/{OWNER_USERNAME})__",
                        disable_web_page_preview=True
                    )
                    return
            except UserNotParticipant:
                 await app.send_message(
                    chat_id=message.chat.id,
                    text="<i>🔐 Join Channel To Use Me 🔐</i>",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("🔓 Join Now 🔓", url=f"https://t.me/{UPDATES_CHANNEL}")
                            ]
                        ]
                    ),

                )
                 return
            except Exception:
                await app.send_message(
                    chat_id=message.chat.id,
                    text=f"<i>Something went wrong</i> <b> <a href='https://telegram.me/{OWNER_USERNAME}'>CLICK HERE FOR SUPPORT </a></b>",

                    disable_web_page_preview=True)
                return
    await app.send_message(message.chat.id, HELP_TEXT, reply_to_message_id=message.id, disable_web_page_preview=True)

@app.on_message(filters.command(["authorize"]))
async def send_help(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    if message.chat.id in ADMIN_LIST or message.from_user.id in ADMIN_LIST :
        try :
            msg = int(message.text.split()[-1])
        except ValueError:
            await app.send_message(message.chat.id, f"Example\n<code>/authorize -100</code>", reply_to_message_id=message.id, disable_web_page_preview=True)
            return
        if msg in GROUP_ID:
            await app.send_message(message.chat.id, f"Already Added", reply_to_message_id=message.id, disable_web_page_preview=True)
        else :
            GROUP_ID.append(msg)
            await app.send_message(message.chat.id, f"Authorized Temporarily!", reply_to_message_id=message.id, disable_web_page_preview=True)
    else:
        await app.send_message(message.chat.id, f"This Command Is Only For Admins", reply_to_message_id=message.id, disable_web_page_preview=True)

@app.on_message(filters.command(["unauthorize"]))
async def send_help(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    if message.chat.id in ADMIN_LIST or message.from_user.id in ADMIN_LIST :
        try :
            msg = int(message.text.split()[-1])
        except ValueError:
            await app.send_message(message.chat.id, f"Example\n<code>/unauthorize -100</code>", reply_to_message_id=message.id, disable_web_page_preview=True)
            return
        if msg not in GROUP_ID:
            await app.send_message(message.chat.id, f"Already Removed", reply_to_message_id=message.id, disable_web_page_preview=True)
        else :
            if msg == int(PERMANENT_GROUP) :
                await app.send_message(message.chat.id, f"Even Owner Can't Remove This {msg} Chat 😂😂", reply_to_message_id=message.id, disable_web_page_preview=True)
                return
            GROUP_ID.remove(msg)
            await app.send_message(message.chat.id, f"Unauthorized!", reply_to_message_id=message.id, disable_web_page_preview=True)
    else:
        await app.send_message(message.chat.id, f"This Command Is Only For Admins", reply_to_message_id=message.id, disable_web_page_preview=True)

@app.on_message(filters.command(["addsudo"]))
async def send_help(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    if message.chat.id == int(OWNER_ID) or message.from_user.id == int(OWNER_ID) :
        try :
            msg = int(message.text.split()[-1])
        except ValueError:
            await app.send_message(message.chat.id, f"Example\n<code>/addsudo 123</code>", reply_to_message_id=message.id, disable_web_page_preview=True)
            return
        if msg in ADMIN_LIST:
            await app.send_message(message.chat.id, f"Already Admin", reply_to_message_id=message.id, disable_web_page_preview=True)
        else :
            ADMIN_LIST.append(msg)
            await app.send_message(message.chat.id, f"Promoted As Admin Temporarily", reply_to_message_id=message.id, disable_web_page_preview=True)
    else:
        await app.send_message(message.chat.id, f"This Command Is Only For Owner", reply_to_message_id=message.id, disable_web_page_preview=True)
        
@app.on_message(filters.command(["remsudo"]))
async def send_help(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    if message.chat.id == int(OWNER_ID) or message.from_user.id == int(OWNER_ID) :
        try :
            msg = int(message.text.split()[-1])
        except ValueError:
            await app.send_message(message.chat.id, f"Example\n<code>/remsudo 123</code>", reply_to_message_id=message.id, disable_web_page_preview=True)
            return
        if msg not in ADMIN_LIST:
            await app.send_message(message.chat.id, f"Already Demoted!", reply_to_message_id=message.id, disable_web_page_preview=True)
        else :
            if msg == int(message.from_user.id) :
                await app.send_message(message.chat.id, f"You Can't Remove Yourself 😂😂", reply_to_message_id=message.id, disable_web_page_preview=True)
                return
            elif msg == int(OWNER_ID) :
                await app.send_message(message.chat.id, f"Even Owner Can't Remove Himself 😂😂", reply_to_message_id=message.id, disable_web_page_preview=True)
                return
            ADMIN_LIST.remove(msg)
            await app.send_message(message.chat.id, f"Demoted!", reply_to_message_id=message.id, disable_web_page_preview=True)
    else:
        await app.send_message(message.chat.id, f"This Command Is Only For Owner", reply_to_message_id=message.id, disable_web_page_preview=True)
        
@app.on_message(filters.command(["users"]))
async def send_help(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    if message.chat.id in ADMIN_LIST or message.from_user.id in ADMIN_LIST :
        lol = "List Of Authorized Chats\n\n"
        for i in GROUP_ID:
            lol += "<code>" + str(i) + "</code>\n"
        lol += "\nList Of Admin ID's\n\n"
        for i in ADMIN_LIST:
            lol += "<code>" + str(i) + "</code>\n"
        await app.send_message(message.chat.id, lol, reply_to_message_id=message.id, disable_web_page_preview=True)
    else :
        await app.send_message(message.chat.id, f"This Command Is Only For Admins", reply_to_message_id=message.id, disable_web_page_preview=True)

# links
@app.on_message(filters.text)
async def receive(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    if str(message.chat.id).startswith("-100") and message.chat.id not in GROUP_ID:
        return
    elif message.chat.id not in GROUP_ID:
        if UPDATES_CHANNEL != "None":
            try:
                user = await app.get_chat_member(UPDATES_CHANNEL, message.chat.id)
                if user.status == enums.ChatMemberStatus.BANNED:
                    await app.send_message(
                        chat_id=message.chat.id,
                        text=f"__Sorry, you are banned. Contact My [ Owner ](https://telegram.me/{OWNER_USERNAME})__",
                        disable_web_page_preview=True
                    )
                    return
            except UserNotParticipant:
                 await app.send_message(
                    chat_id=message.chat.id,
                    text="<i>🔐 Join Channel To Use Me 🔐</i>",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("🔓 Join Now 🔓", url=f"https://t.me/{UPDATES_CHANNEL}")
                            ]
                        ]
                    ),

                )
                 return
            except Exception:
                await app.send_message(
                    chat_id=message.chat.id,
                    text=f"<i>Something went wrong</i> <b> <a href='https://telegram.me/{OWNER_USERNAME}'>CLICK HERE FOR SUPPORT </a></b>",

                    disable_web_page_preview=True)
                return
    bypass = threading.Thread(target=lambda:loopthread(message),daemon=True)
    bypass.start()


# doc thread
def docthread(message):
    if message.document.file_name.endswith("dlc"):
        msg = app.send_message(message.chat.id, "🔎 __bypassing...__", reply_to_message_id=message.id)
        print("sent DLC file")
        sess = requests.session()
        file = app.download_media(message)
        dlccont = open(file,"r").read()
        link = bypasser.getlinks(dlccont,sess)
        app.edit_message_text(message.chat.id, msg.id, f'__{link}__')
        os.remove(file)

@app.on_message(filters.document)
async def docfile(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    if str(message.chat.id).startswith("-100") and message.chat.id not in GROUP_ID:
        return
    elif message.chat.id not in GROUP_ID:
        if UPDATES_CHANNEL != "None":
            try:
                user = await app.get_chat_member(UPDATES_CHANNEL, message.chat.id)
                if user.status == enums.ChatMemberStatus.BANNED:
                    await app.send_message(
                        chat_id=message.chat.id,
                        text=f"__Sorry, you are banned. Contact My [ Owner ](https://telegram.me/{OWNER_USERNAME})__",
                        disable_web_page_preview=True
                    )
                    return
            except UserNotParticipant:
                 await app.send_message(
                    chat_id=message.chat.id,
                    text="<i>🔐 Join Channel To Use Me 🔐</i>",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("🔓 Join Now 🔓", url=f"https://t.me/{UPDATES_CHANNEL}")
                            ]
                        ]
                    ),

                )
                 return
            except Exception:
                await app.send_message(
                    chat_id=message.chat.id,
                    text=f"<i>Something went wrong</i> <b> <a href='https://telegram.me/{OWNER_USERNAME}'>CLICK HERE FOR SUPPORT </a></b>",

                    disable_web_page_preview=True)
                return
    if message.document.file_name.endswith(".dlc"):
        bypass = threading.Thread(target=lambda:docthread(message),daemon=True)
        bypass.start()

# files
@app.on_message([filters.document, filters.photo, filters.video])
def docfile(
    client: Client,
    message: Message,
):

    try:
        if message.document.file_name.endswith("dlc"):
            bypass = Thread(target=lambda: docthread(message), daemon=True)
            bypass.start()
            return
    except:
        pass

    bypass = Thread(target=lambda: loopthread(message, True), daemon=True)
    bypass.start()


# server loop
print("Bot Starting")
app.run()
