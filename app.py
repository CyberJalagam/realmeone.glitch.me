# For realmeone.glitch.me // realmeone.surge.sh // realmeone.herokuapp.com
# By Priyam Kalra

from os import rename, path
from time import sleep
from random import choice
from git import Repo, Actor
from datetime import date as Date
from shutil import rmtree, copytree
from telethon.extensions.html import unparse
from jinja2 import Environment, FileSystemLoader


CWD = ENV.GLITCH_APP


async def main(e):
    raw_data = []
    data = {}
    date = Date.today().strftime("%B %d, %Y")
    log(date + " -- its update day!", "Updates chat(s): " +
        str(ENV.CHATS), "Event chat: " + f"@{(await e.get_chat()).username}")
    if path.exists(CWD):
        rmtree(CWD)
    gl = Repo.clone_from(ENV.GLITCH_GIT_URL, CWD)
    for chat in ENV.CHATS:
        async for msg in client.iter_messages(chat):
            if not validate(msg):
                continue
            raw_data.append(msg)
    for msg in sorted(raw_data, key=lambda e: e.date, reverse=True):
        text = parse_text(msg)
        title = msg.message.split()[0][1:]
        if title in ENV.BLOCKED:
            continue
        if title.lower() not in str(data.keys()).lower():
            data.update({title: text})
            logo = await get_media(msg, title)
            parse_template(title=title, text=text[len(title)+1:], logo=logo)
    parsed_data = parse_data(data)
    parse_template(title="index.html", roms=sorted(parsed_data[0][1:], key=lambda e: e.upper()), kernels=sorted(parsed_data[1][1:], key=lambda e: e.upper()), recoveries=sorted(parsed_data[2][1:], 
        key=lambda e: e.upper()), latest=[parsed_data[0][1], parsed_data[1][1], parsed_data[2][1]], count=[parsed_data[0][0], parsed_data[1][0], parsed_data[2][0]], get_color=get_color, choice=choice, date=date)
    log("Update completed.")
    deploy(gl)
    log("All jobs executed, idling..")


async def get_media(msg, title):
    media = await client.download_media(msg, f"{CWD}/{title}/")
    if media.endswith((".png", ".jpg", ".jpeg")):
        logo_path = f"{CWD}/{title}/logo.png"
        logo = f"<img src='https://{CWD}.glitch.me/{title}/logo.png' class='image'>"
    elif media.endswith((".mp4")):
        logo_path = f"{CWD}/{title}/logo.mp4"
        logo = f"<video style='border-radius: 10px;' height=255 autoplay loop muted playsinline><source src='https://{CWD}.glitch.me/{title}/logo.mp4' type='video/mp4'></video>"
    rename(media, logo_path)
    return logo


def parse_text(msg):
    text = unparse(msg.message, msg.entities)
    changes = {"<em>": "", "</em>": "", "<strong>": "",
               "</strong>":"", "\n": "\n<br>", "▪️": "> "}
    for word in text.split():
        word = word.replace("<strong>", "").replace("</strong>", "")
        if word.startswith("@"):
            changes.update({word: f"<a href=\"https://t.me/{word[1:]}\">{word}</a>"})
    for a, b in changes.items():
        text = text.replace(a, b)
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
    path = f"{CWD}/{title}/index.html"
    to_path = None
    if title.endswith(".html"):
        path = f"glitch/{title}"
        to_path = f"{CWD}/{title}"
        jinja2_template = str(open(path, "r").read())
    else:
        kwargs["title"] = title
        jinja2_template = str(open("glitch/template.html", "r").read())
    template_object = Environment(
        loader=FileSystemLoader("glitch")).from_string(jinja2_template)
    static_template = template_object.render(**kwargs)
    with open(to_path or path, "w") as f:
        f.write(static_template)


def validate(msg):
    text = msg.text or ""
    for req in ENV.FILTERS:
        if f"#{req.lower()}" in text.lower():
            return True
    return False


async def auth(e):
    chat = await e.get_chat()
    try:
        if f"@{chat.username}" in ENV.CHATS:
            return True
    except:
        pass
    return False


def log(*text):
    for item in text:
        logger.info(item)
        if len(text) > 1:
            sleep(1)


def deploy(gl):
    if path.isdir(f"glitch/static"):
        copytree(f"glitch/static", f"{CWD}/static", dirs_exist_ok=True)
    actor = Actor(f"Glitch ({CWD})", "None")
    gl.index.add("*")
    gl.index.write()
    commit = gl.index.commit("Automatic deploy", author=actor, committer=actor)
    push = gl.remote().push()[0]
    if str(commit)[:7] in push.summary:
        log(f"{CWD}.glitch.me deployed successfully!")
    else:
        log("Error while deploying:\n" + push.summary,
            str(commit), str(commit)[:7])


def get_color():
    return f"hsl({choice(range(359))}, 100%, 75%)"


@client.on(events(incoming=True, outgoing=True, forwards=True, func=auth))
async def run(e):
    await main(e)

@client.on(events(pattern="glitch", allow_sudo=True))
async def trigger(e):
    await e.reply(f"**Manual Update** `--` @{(await e.get_sender()).username}!\n`{CWD}.glitch.me`")
    await main(e)
