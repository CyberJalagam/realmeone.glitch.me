# For realmeone.glitch.me
# By justaprudev

import os
import json
import shutil
import datetime
from pathlib import Path
from urllib.parse import urlparse
from telethon.extensions import html
from git import Repo, Actor, GitCommandError
from jinja2 import Environment, FileSystemLoader

NAME = Path(__file__).stem
DATA = {
    "chats": ENV.CHATS or ["@username"],
    "item_types": ["rom", "kernel", "recovery"],
    "blocked_items": ENV.BLOCKED or [],
    "filters": ENV.FILTERS or ["rom", "kernel", "recovery"],
    "git": ENV.GLITCH_GIT_URL or None,
}
GIT_URL = urlparse(DATA["git"])
APP_NAME = Path(GIT_URL.path).stem # Path(DATA["git"].split("/")[-1])
CWD = Path(__file__).parent
TARGET_DIRECTORY = CWD / APP_NAME
GLITCH_FOLDER = CWD / "glitch"
DOMAIN = f"{APP_NAME}.glitch.me"
DATE = datetime.date.today().strftime("%B %d, %Y")


@client.on(events(incoming=True, outgoing=True, forwards=True,
    func=lambda e: f"@{e.chat.username}" in DATA["chats"] if e.chat else False,
))
@client.on(events(pattern=APP_NAME, allow_sudo=True))
async def glitch(e):
    if (await e.get_sender()).username == me.username:
        await e.delete()
    await e.reply(f"Manual Update - {APP_NAME}.glitch.me")
    if not DATA:
        logger.info(f"Initialization failed!")
        return
    logger.info(
        f"{DATE} -- its update day!"
        + f"\nUpdates chat(s): {DATA['chats']}"
        + f"\nEvent chat: @{(await e.get_chat()).username}"
    )
    if TARGET_DIRECTORY.exists():
        shutil.rmtree(TARGET_DIRECTORY)
    logger.info("Cloning glitch repository..")
    glitch_repository = await clone_from_glitch(DATA["git"])
    titles = {key: [] for key in DATA["item_types"]}
    for i in titles:
        Path.mkdir(TARGET_DIRECTORY / i, exist_ok=True)
    Path.mkdir(TARGET_DIRECTORY / "about", exist_ok=True)
    os.rename(TARGET_DIRECTORY/"files/rom.html", TARGET_DIRECTORY/"rom/index.html")
    os.rename(TARGET_DIRECTORY/"files/kernel.html", TARGET_DIRECTORY/"kernel/index.html")
    os.rename(TARGET_DIRECTORY/"files/recovery.html", TARGET_DIRECTORY/"recovery/index.html")
    os.rename(TARGET_DIRECTORY/"about.html", TARGET_DIRECTORY/"about/index.html")
    msgs = []
    for chat in DATA["chats"]:
        async for msg in client.iter_messages(chat):
            content = msg.message or "#"
            title = content.split()[0][1:]
            if (
                not title
                or not is_required_content(content.lower())
                or title.lower() in map(str.lower, DATA["blocked_items"])
            ):
                continue
            msgs.append(msg)
            
    for msg in sorted(msgs, key=lambda e: e.date, reverse=True):
        content = msg.message.strip()
        title = shorten(content.split()[0][1:])
        lower_content, lower_title = content.lower(), title.lower()
        for content_type in titles:
            content_list = titles[content_type]
            if f"#{content_type}" in lower_content and lower_title not in map(
                str.lower, content_list
            ):
                content_list.append(title)
                path = TARGET_DIRECTORY / content_type / lower_title
                path.mkdir(exist_ok=True)
                banner = await get_banner(msg, path)
                html_content = html.unparse(content, msg.entities)
                _date = msg.date.strftime("%B %d, %Y")
                write_webpage(
                    path_list=path,
                    title=title,
                    content=parse_content(html_content.split(' ', maxsplit=1)[1].strip()),
                    banner=banner,
                    date=_date
                )
    logger.info(json.dumps(titles, sort_keys=True, indent=1))
    path_list = []
    for subdir, dir, files in os.walk(TARGET_DIRECTORY):
        for file in files:
            if file == "index.html":
                path_list.append(os.path.join(subdir, file))
    write_webpage(
        path_list=path_list,
        roms=remove_duplicates(titles["rom"]),
        kernels=remove_duplicates(titles["kernel"]),
        recoveries=remove_duplicates(titles["recovery"]),
        get_random_color=get_random_color,
        len=len,
        date=DATE,
    )
    push_to_glitch(glitch_repository)
    logger.info("Update completed.")


async def get_banner(msg, path: Path) -> str:
    # Declared twice for the sake of readability
    media = await client.download_media(msg, path)
    media = Path(media)
    path /= "banner" + media.suffix
    parents = list(map(lambda i: i.stem, path.parents))
    if media.suffix == ".mp4":
        banner = (
            "<video autoplay loop muted playsinline>"
            f"<source src='https://{DOMAIN}/{parents[1]}/{parents[0]}/{path.name}' type='video/mp4'>"
            "</video>"
        )
    else:
        path = path.with_suffix(".png")
        banner = f"<img src='https://{DOMAIN}/{parents[1]}/{parents[0]}/{path.name}' height='255'>"
    media.rename(path)
    return banner


def parse_content(content) -> str:
    replacements = {
        "<strong>": "",
        "</strong>": "",
        "<em>": "",
        "</em>": "",
        "t.me": "telegram.me",
        "\n": "\n      <br>",
    }
    for old, new in replacements.items():
        content = content.replace(old, new)
    for i in content.split():
        if i.startswith("@"):
            content = content.replace(i, f"<a href=https://telegram.me/{i[1:]}>{i}</a>")
    return content


def write_webpage(path_list, title=None, **variables) -> None:
    if title:
        path = Path(path_list) / "index.html"
        variables["title"] = title
        jinja2_template = open(GLITCH_FOLDER / "files" / "template.html", "r").read()
        template_object = Environment(loader=FileSystemLoader(GLITCH_FOLDER)).from_string(jinja2_template)
        with open(path, "w") as f:
            f.write(template_object.render(**variables))
    else:
        for i in path_list:
            path = Path(i)
            jinja2_template = open(path, "r").read()
            template_object = Environment(loader=FileSystemLoader(GLITCH_FOLDER)).from_string(jinja2_template)
            with open(path, "w") as f:
                f.write(template_object.render(**variables))


async def clone_using_shell(git_url, path: Path) -> Repo:
    if path.exists():
        shutil.rmtree(path)
    shell_output = await client.shell(f"git clone -v {git_url} {path}")
    logger.info(shell_output)
    return Repo(path)

async def clone_from_glitch(git_url) -> Repo:
    # GitPython can't clone from glitch anymore for some reason
    # repo = Repo.clone_from(git_url, TARGET_DIRECTORY)
    repo = await clone_using_shell(git_url, TARGET_DIRECTORY)
    
    logger.info("Cleaning up old files..")
    glitch_cleanup(TARGET_DIRECTORY)

    logger.info("Copying new files..")
    shutil.copytree(GLITCH_FOLDER, TARGET_DIRECTORY, dirs_exist_ok=True)
    return repo

def glitch_cleanup(glitch) -> None:
    for subdir, dirs, files in os.walk(glitch):
        for filename in files:
            path = os.path.join(subdir, filename)
            if ".git" not in path and filename != ".glitch-assets":
                os.remove(path)
        for dir in dirs:
            path = os.path.join(subdir, dir)
            if ".git" not in path:
                shutil.rmtree(path)
    

def push_to_glitch(repo: Repo) -> None:
    actor = Actor(f"Glitch ({APP_NAME})", "none")
    origin = repo.remote()
    index = repo.index
    index.add("*")
    commit = str(
        index.commit(
            # Glitch's signature commit message
            "Checkpoint 🚀",
            author=actor,
            committer=actor,
        )
    )
    push = origin.push(force=True)[0]
    logger.info(
        f"{DOMAIN} deployed successfully!"
        if commit[:7] in push.summary
        else f"Error while deploying:\n{push.summary}\n{commit}"
    )


def is_required_content(content) -> bool:
    for i in DATA["filters"]:
        if f"#{i}" in content:
            return True
    return False


def shorten(title) -> str:
    while len(title) > 17:
        x = 0
        for i in reversed(title):
            x += 1
            if x == 17:
                title = title[:17]
                break
            if i.isupper():
                title = title[:-x]
                break
    return title
        

def get_random_color() -> str:
    from random import randint
    return f"hsl({randint(0, 359)}, 100%, 75%)"


def remove_duplicates(l: list) -> list:
    # This is the equivalent of list(set(l)) but it preserves the order of the list
    return list(dict.fromkeys(l))
