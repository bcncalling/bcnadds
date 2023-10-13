import random
import os
import asyncio
from pyrogram import Client

async def customize():
    rem = None
    try:
        chat_id = "LOG_CHANNEL" 
        if app.get_me().photo:
            return
        print("Customizing Your Assistant Bot in @BOTFATHER")
        UL = f"@{app.get_me().username}"
        bcn = app.get_me()
        if not bcn.username:
            sir = bcn.first_name
        else:
            sir = f"@{bcn.username}"
        
        file = random.choice(
            [
                "https://telegra.ph/file/92cd6dbd34b0d1d73a0da.jpg",
                "https://telegra.ph/file/a97973ee0425b523cdc28.jpg",
                "resources/extras/ultroid_assistant.jpg",
            ]
        )
        
        if not os.path.exists(file):
            # You need to implement a download_file function to download the file
            # file = await download_file(file, "profile.jpg")
            rem = True
        
        msg = await app.send_message(chat_id, "**Auto Customisation** Started on @Botfather")
        await asyncio.sleep(1)
        
        # Send commands to BotFather
        await bot.send_message("botfather", "/cancel")
        await asyncio.sleep(1)
        await bot.send_message("botfather", "/setuserpic")
        await asyncio.sleep(1)
        isdone = (await bot.get_history("botfather", limit=1))[-1].text
        
        if isdone.startswith("Invalid bot"):
            print("Error while trying to customize assistant, skipping...")
            return
        
        await bot.send_message("botfather", UL)
        await asyncio.sleep(1)
        await bot.send_document("botfather", file)
        await asyncio.sleep(2)
        await bot.send_message("botfather", "/setabouttext")
        await asyncio.sleep(1)
        await bot.send_message("botfather", UL)
        await asyncio.sleep(1)
        await bot.send_message("botfather", f"✨ Hello ✨!! I'm Assistant Bot of {sir}")
        await asyncio.sleep(2)
        await bot.send_message("botfather", "/setdescription")
        await asyncio.sleep(1)
        await bot.send_message("botfather", UL)
        await asyncio.sleep(1)
        await bot.send_message("botfather", f"Developed and designed by @Blackcatfighters & @blackcatserver")
        await asyncio.sleep(2)
        await msg.edit("Completed **Auto Customisation** at @BotFather.")
        if rem:
            os.remove(file)
        print("Customization Done")
    except Exception as e:
        print(e)
