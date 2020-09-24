# For realmeone.surge.sh
# By Priyam Kalra

from time import sleep
from random import choice
from shutil import rmtree
from production import Config
from datetime import date as datetime
from subprocess import check_output, DEVNULL
from telethon.extensions.html import unparse
from os import rename, listdir, remove, path
from jinja2 import Environment, FileSystemLoader


# Checks chat username
async def chat(e):
    chat = await e.get_chat()
    if f"@{chat.username}" in Config.CHATS:
        return True
    return False


# Event Dispatchers
@client.on(register(outgoing=True, func=chat))
async def manual(event):
    log("Starting jobs for manual update.")
    await handler(event)


@client.on(register(incoming=True, func=chat))
async def automatic(event):
    log("Starting jobs for automatic update.")
    await handler(event)


# Event handler
async def handler(event):
    data = {}
    messages = []
    date = datetime.today().strftime("%B %d, %Y")
    chats = Config.CHATS
    log([date + " -- its update day!", "Updates chat(s): " +
         str(chats), "Event chat: " + f"@{event.sender.username}"])
    for chat in chats:
        async for message in client.iter_messages(chat):
            messages.append(message)
    messages = sorted(messages, key=latest, reverse=True)
    for message in messages:
        if is_valid(message.text):
            text = parse_text(message)
            initial = f"{text.split('#')[1].strip()}"
            title = initial[:1].upper() + initial[1:]
            if title not in Config.BLOCKED_UPDATES:
                with open("surge/index.html", "r") as index:
                    with open("index.bak", "w") as backup:
                        backup.write(index.read())
                if title.lower() not in str(data.keys()).lower():
                    data.update({title: text})
                    media = await client.download_media(message, f"surge/{title}/")
                    if media.endswith((".png", ".jpg", ".jpeg")):
                        logo = f"surge/{title}/logo.png"
                        logo_html = f"<img src='https://realmeone.surge.sh/{title}/logo.png' height='255'>"
                    elif media.endswith((".mp4")):
                        logo = f"surge/{title}/logo.mp4"
                        logo_html = f"<video style='border-radius: 10px;' height=255 autoplay loop muted playsinline><source src='https://realmeone.surge.sh/{title}/logo.mp4' type='video/mp4'></video>"
                    rename(media, logo)
                    parse_template(title=title, text=text[len(title)+1:], logo=logo_html)
    parsed_data = parse_data(data)
    parse_template(title="404.html")
    parse_template(title="index.html", roms=sorted(parsed_data[0][1:]), kernels=sorted(parsed_data[1][1:]), recoveries=sorted(
        parsed_data[2][1:]), latest=[parsed_data[0][1], parsed_data[1][1], parsed_data[2][1]], count=[parsed_data[0][0], parsed_data[1][0], parsed_data[2][0]], random_pastel=random_pastel, choice=choice, date=date)
    log("Update completed.")
    deploy()
    log("Cleaning up leftover files..")
    for f in listdir("surge"):
        if path.isdir(f"surge/{f}"):
            if f != "static":
                rmtree(f"surge/{f}")
    remove("surge/index.html")
    rename("index.bak", "surge/index.html")
    log(["Cleaned up all leftover files.", "All jobs executed, idling.."])


# Helpers
def parse_text(msg):
    text = unparse(msg.message, msg.entities)
    changes = {"▪️": "> ", "\n": "\n<br>"}
    for a, b in changes.items():
        text = text.replace(a, b)
    for term in text.split():
        if term.startswith("@"):
            text = text.replace(term, f"<a href=\"http://t.me/{term[1:]}\">{term}</a>")
    return text


def parse_data(data):
    roms = [0]
    kernels = [0]
    recoveries = [0]
    for title, value in data.items():
        value = value.lower()
        if "#rom" in value:
            roms.append(title)
            roms[0] += 1
        elif "#blissrom" in value:
            roms.append(title)
            roms[0] += 1
        elif "#kernel" in value:
            kernels.append(title)
            kernels[0] += 1
        elif "#recovery" in value:
            recoveries.append(title)
            recoveries[0] += 1
    return [roms, kernels, recoveries]


def parse_template(title, **kwargs):
    path = f"surge/{title}/index.html"
    if title.endswith(".html"):
        path = f"surge/{title}"
        jinja2_template = str(open(path, "r").read())
    else:
        kwargs["title"] = title
        jinja2_template = str(open("surge/template.html", "r").read())
    template_object = Environment(
        loader=FileSystemLoader("surge")).from_string(jinja2_template)
    static_template = template_object.render(**kwargs)
    with open(path, "w") as f:
        f.write(static_template)


def latest(message):
    return message.date


def is_valid(msg):
    text = msg if msg is not None else ""
    for req in Config.FILTERS:
        if f"#{req.lower()}" in text.lower():
            return True
    return False
    

def log(text):
    if type(text) is not list:
        text = [text]
    for item in text:
        logger.info(item)
        sleep(1)


def random_pastel():
    return f"hsl({choice(range(359))}, 100%, 75%)"


def deploy():
    log(f"Deploying {Config.SUBDOMAIN}.surge.sh..")
    output = check_output(
        f"surge surge https://{Config.SUBDOMAIN}.surge.sh", shell=True)
    if "Success!" in str(output):
        log(f"{Config.SUBDOMAIN}.surge.sh deployed sucessfully.")
    else:
        log(f"Failed to deploy {Config.SUBDOMAIN}.surge.sh " +
            "\nError: " + str(output))
