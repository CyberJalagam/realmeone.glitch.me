# For curtana.surge.sh
# By Priyam Kalra

import os
import sys
import asyncio
from web import WebUtils
from time import sleep


def required(text):
    return True if "#ROM" in text else (True if "#Kernel" in text else (True if "#Recovery" in text else False))


@bot.on(command(incoming=True, func=lambda event: str(event.sender_id) in Config.AUTH_CHATS))
async def watcher(event):
    """
    Watches @curtanaupdates for new rom/kernel/recovery updates
    """
    web = WebUtils(logger)
    logger.info(web.today + " -- its update day!")
    messages = []
    logger.info("Authenticated chat: " + str(event.sender_id))
    chats = Config.UPDATE_CHATS
    logger.info("Updates chat(s): " + str(chats))
    logger.info("Starting update..")
    for chat in chats:
        async for message in bot.iter_messages(chat):
            messages.append(message)
    for message in messages:
        text = message.text if message.text is not None else ""
        if not required(text):
            continue
        head = f"{text.split()[0][1:]}"
        if head in Config.BLOCKED_UPDATES:
            continue
        with open("surge/index.html", "r") as a:
            with open("index.bak", "w") as b:
                b.write(a.read())
        if head.lower() not in str(web.data.keys()).lower():
            web.data.update({head: text})
            image = await bot.download_media(message, f"surge/{head}/")
            thumbnails = []
            thumbnail = f"surge/{head}/thumbnail.png"
            os.rename(image, thumbnail)
            thumbnails.append(thumbnail)
            web.save(head)
    web.refresh()
    logger.info("Update complete.")
    sleep(1)
    logger.info("Deploying curtana.surge.sh")
    web.deploy()
    sleep(1)
    logger.info("Cleaning up leftover files..")
    for file in thumbnails:
        os.remove(file)
    os.remove("surge/index.html")
    os.rename("index.bak", "surge/index.html")
    logger.info("All jobs executed, idling..")
