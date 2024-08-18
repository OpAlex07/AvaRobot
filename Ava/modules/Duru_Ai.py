import requests
import aiofiles
import aiohttp
import asyncio
import os
import uuid
import base64
import mimetypes
import shutil
from re import findall
from pyrogram import Client, filters
from pyrogram.enums import ChatAction, ParseMode, MessageMediaType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Message
from bing_image_downloader import downloader
import httpx
import config
from Ava import DEEP_API, Jarvis as app
from MukeshAPI import api
from lexica.constants import languageModels
from httpx import AsyncClient

# Ava as an Ai Assistant
@app.on_message(filters.command(["uru"], prefixes=["D"]))
async def chat_gpt(bot, message):
    try:
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        
        name = message.from_user.first_name if message.from_user else "User"
        
        if len(message.command) < 2:
            await message.reply_text(f"Hello {name}, How can I help you today?")
        else:
            query = message.text.split(' ', 1)[1]
            response = api.gemini(query)["results"]
            await message.reply_text(f"{response}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await message.reply_text(f"Error: {e}")

# Upscale feature
async def load_image(image_path: str, url: str) -> str:
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                async with aiofiles.open(image_path, mode="wb") as file:
                    await file.write(await response.read())
                return image_path
            return None

@app.on_message(filters.command("upscale", prefixes=["/", ".", "!"]))
async def upscale_image(client, message):
    chat_id = message.chat.id
    replied_message = message.reply_to_message
    
    if not DEEP_API:
        return await message.reply_text("I can't upscale without a DEEP API key!")
    
    if not replied_message or not replied_message.photo:
        return await message.reply_text("Please reply to an image.")
    
    aux_message = await message.reply_text("Upscaling, please wait...")
    image_path = await replied_message.download()
    
    response = requests.post(
        "https://api.deepai.org/api/torch-srgan",
        files={'image': open(image_path, 'rb')},
        headers={'api-key': DEEP_API}
    ).json()
    
    image_url = response.get("output_url")
    if not image_url:
        return await aux_message.edit("Failed to upscale image, please try again.")
    
    downloaded_image = await load_image(image_path, image_url)
    if not downloaded_image:
        return await aux_message.edit("Failed to download upscaled image, please try again.")
    
    await aux_message.delete()
    await message.reply_document(document=downloaded_image)

@app.on_message(filters.command("draw", prefixes=["/", ".", "!"])
async def draw_image(client, message):
    chat_id = message.chat.id
    user_id = message.sender_chat.id if message.sender_chat else message.from_user.id
    replied_message = message.reply_to_message
    
    if not DEEP_API:
        return await message.reply_text("I can't generate images without a DEEP API key!")
    
    if replied_message and replied_message.text:
        query = replied_message.text
    elif len(message.text.split()) > 1:
        query = message.text.split(None, 1)[1]
    else:
        return await message.reply_text("Please provide text or reply to a text message.")
    
    aux_message = await message.reply_text("Generating image, please wait...")
    image_path = f"cache/{user_id}_{chat_id}_{message.id}.png"
    
    response = requests.post(
        "https://api.deepai.org/api/text2img",
        data={'text': query, 'grid_size': '1', 'image_generator_version': 'hd'},
        headers={'api-key': DEEP_API}
    ).json()
    
    image_url = response.get("output_url")
    if not image_url:
        return await aux_message.edit("Failed to generate image, please try again.")
    
    downloaded_image = await load_image(image_path, image_url)
    if not downloaded_image:
        return await aux_message.edit("Failed to download generated image, please try again.")
    
    await aux_message.delete()
    await message.reply_photo(photo=downloaded_image, caption=query)

# Image searching
@app.on_message(filters.command(["img", "image"], prefixes=["/", ".", "!"]))
async def google_img_search(client: Client, message: Message):
    chat_id = message.chat.id

    try:
        query = message.text.split(None, 1)[1]
    except IndexError:
        return await message.reply("Provide an image query to search!")

    lim = findall(r"lim=\d+", query)
    try:
        lim = int(lim[0].replace("lim=", ""))
        query = query.replace(f"lim={lim}", "")
    except IndexError:
        lim = 10  # Default limit to 5 images

    download_dir = "downloads"

    try:
        downloader.download(query, limit=lim, output_dir=download_dir, adult_filter_off=True, force_replace=False, timeout=60)
        images_dir = os.path.join(download_dir, query)
        if not os.listdir(images_dir):
            raise Exception("No images were downloaded.")
        lst = [os.path.join(images_dir, img) for img in os.listdir(images_dir)][:lim]  # Ensure we only take the number of images specified by lim
    except Exception as e:
        return await message.reply(f"Error in downloading images: {e}")

    msg = await message.reply("`=> Dᴜʀᴜ Scraping images...`")

    count = 0
    for img in lst:
        count += 1
        await msg.edit(f"`Dᴜʀᴜ Scrapped images {count}`")

    try:
        await app.send_media_group(
            chat_id=chat_id,
            media=[InputMediaPhoto(media=img) for img in lst],
            reply_to_message_id=message.id
        )
        shutil.rmtree(images_dir)
        await msg.delete()
    except Exception as e:
        await msg.delete()
        return await message.reply(f"Error in sending images: {e}")


#reverse

ENDPOINT = "https://sasta-api.vercel.app/googleImageSearch"
httpx_client = httpx.AsyncClient(timeout=60)

COMMANDS = [
    "reverse",
    "grs"
    "gis",
    "pp"
    ]

class STRINGS:
    REPLY_TO_MEDIA = "ℹ️ Please reply to a message that contains one of the supported media types, such as a photo, sticker, or image file."
    UNSUPPORTED_MEDIA_TYPE = "⚠️ <b>Unsupported media type!</b>\nℹ️ Please reply with a supported media type: image, sticker, or image file."
    
    REQUESTING_API_SERVER = "Requesting to <b>API Server</b>..."
    
    DOWNLOADING_MEDIA = "Downloading media..."
    UPLOADING_TO_API_SERVER = "Uploading media to <b>API Server</b>... "
    PARSING_RESULT = "Parsing result..."
    
    EXCEPTION_OCCURRED = "❌ <b>Exception occurred!</b>\n\n<b>Exception:</b> {}"
    
    RESULT = """
  <b>Query:</b> {query}
  <b>Page Link:</b> <a href="{search_url}">Link</a>

  <b>Time Taken:</b> <code>{time_taken}</code> ms.
    """
    OPEN_SEARCH_PAGE = "Open"

@app.on_message(filters.command(COMMANDS))
async def on_google_lens_search(client: Client, message: Message) -> None:
    if len(message.command) > 1:
        image_url = message.command[1]
        params = {
            "image_url": image_url
        }
        status_msg = await message.reply(STRINGS.REQUESTING_API_SERVER)
        start_time = asyncio.get_event_loop().time()
        response = await httpx_client.get(ENDPOINT, params=params)
        
    elif (reply := message.reply_to_message):
        if reply.media not in (MessageMediaType.PHOTO, MessageMediaType.STICKER, MessageMediaType.DOCUMENT):
            await message.reply(STRINGS.UNSUPPORTED_MEDIA_TYPE)
            return
        
        status_msg = await message.reply(STRINGS.DOWNLOADING_MEDIA)
        file_path = f"temp/{uuid.uuid4()}"
        try:
            await reply.download(file_path)
        except Exception as exc:
            text = STRINGS.EXCEPTION_OCCURRED.format(exc)
            await message.reply(text)
            
            try:
                os.remove(file_path)
            except FileNotFoundError:
                pass
            return
        
        with open(file_path, "rb") as image_file:
            start_time = asyncio.get_event_loop().time()
            files = {"file": image_file}
            await status_msg.edit(STRINGS.UPLOADING_TO_API_SERVER)
            response = await httpx_client.post(ENDPOINT, files=files)
        
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass
    
    if response.status_code == 404:
        text = STRINGS.EXCEPTION_OCCURRED.format(response.json()["error"])
        await message.reply(text)
        await status_msg.delete()
        return
    elif response.status_code != 200:
        text = STRINGS.EXCEPTION_OCCURRED.format(response.text)
        await message.reply(text)
        await status_msg.delete()
        return
    
    await status_msg.edit(STRINGS.PARSING_RESULT)
    response_json = response.json()
    query = response_json["query"]
    search_url = response_json["search_url"]
    
    end_time = asyncio.get_event_loop().time() - start_time
    time_taken = "{:.2f}".format(end_time)
    
    text = STRINGS.RESULT.format(
        query=f"<code>{query}</code>" if query else "<i>Name not found</i>",
        search_url=search_url,
        time_taken=time_taken
        )
    buttons = [
        [InlineKeyboardButton(STRINGS.OPEN_SEARCH_PAGE, url=search_url)]
        ]
    await message.reply(text, disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))
    await status_msg.delete()
