import random
import os
import asyncio
from pyrogram import Client
from bcnplugs import app, client

async def customize():
    rem = None
    try:
        chat_id = "-1001916479883" 
        if app.get_me().photo:
            return
        print("Customizing Your Assistant Bot in @Botfather")
        UL = f"@{app.get_me().username}"
        bcn = app.get_me()
        if not bcn.username:
            sir = bcn.first_name
        else:
            sir = f"@{bcn.username}"
        
        msg = await app.send_message(chat_id, "**Auto Customisation** Started on @Botfather")
        await asyncio.sleep(1)
        
        # Send commands to BotFather
        await client.send_message("botfather", "/cancel")
        await asyncio.sleep(1)
        await client.send_message("botfather", "/setuserpic")
        await asyncio.sleep(1)
        isdone = (await client.get_history("botfather", limit=1))[-1].text
        
        if isdone.startswith("Invalid bot"):
            print("Error while trying to customize assistant, skipping...")
            return
        
        await client.send_message("botfather", UL)
        await asyncio.sleep(1)
        await client.send_document("botfather", file)
        await asyncio.sleep(2)
        await client.send_message("botfather", "/setabouttext")
        await asyncio.sleep(1)
        await client.send_message("botfather", UL)
        await asyncio.sleep(1)
        await client.send_message("botfather", f"✨ Hello ✨!! I'm Assistant Bot of {sir}")
        await asyncio.sleep(2)
        await client.send_message("botfather", "/setdescription")
        await asyncio.sleep(1)
        await client.send_message("botfather", UL)
        await asyncio.sleep(1)
        await client.send_message("botfather", f"Developed and designed by @Blackcatfighters & @blackcatserver")
        await asyncio.sleep(2)
        await msg.edit("Completed **Auto Customisation** at @BotFather.")
        if rem:
            os.remove(file)
        print("Customization Done")
    except Exception as e:
        print(e)
