# For curtanax.surge.sh
# By Priyam Kalra

import os
from production import Config
from jinja2 import Environment, FileSystemLoader
from datetime import date
import subprocess


class WebUtils():
    today = date.today().strftime("%B %d, %Y")
    data = {}

    def __init__(self, logger):
        self.logger = logger

    def deploy(self):
        output = subprocess.check_output(
            "surge surge curtana.surge.sh", shell=True)
        if "Success!" in str(output):
            self.logger.info("curtana.surge.sh deployed sucessfully.")
        else:
            self.logger.info(
                "Failed to deploy curtana.surge.sh " + "\nError: " + str(output))

    def parse_message(self, message):
        author = "\n<br>Follow"
        keywords = ["Download", "XDA",
                    "Source changelog", "Support", "Changelog"]
        for line in message.split("\n"):
            for keyword in keywords:
                if f"[{keyword}](" in line:
                    download_link = line.split("(")[-1].split(")")[0]
                    message = message.replace(
                        line, f"▪️<a href='{download_link}'>{keyword}</a>")
            if line.startswith("**By** @"):
                author = f">{line[7:]}</a>\n<br>Follow"
                break
        modifications = {"\n": "\n<br>", "**": "", "__": "",
                         "👉🏻 @CurtanaUpdates": "<a href=https://t.me/curtanaupdates>@curtanaupdates</a>",
                         "👉🏻 @CurtanaOfficial": "<a href=https://t.me/rn9_universal>@rn9_universal</a>",
                         "@CurtanaUpdates": "<a href=https://t.me/curtanaupdates>@curtanaupdates</a>",
                         "@CurtanaOfficial": "<a href=https://t.me/rn9_universal>@rn9_universal</a>",
                         "@curtanaupdates": "<a href=https://t.me/curtanaupdates>@curtanaupdates</a>",
                         "@rn9_universal": "<a href=https://t.me/rn9_universal>@rn9_universal</a>",
                         "@CurtanaCloud": "<a href=https://t.me/curtanaupdates>@curtanacloud</a>",
                         "@CurtanaDiscussion": "<a href=https://t.me/rn9_universal>@curtanadiscussion</a>",
                         "@curtanacloud": "<a href=https://t.me/curtanaupdates>@curtanacloud</a>",
                         "@curtanadiscussion": "<a href=https://t.me/rn9_universal>@curtanadiscussion</a>",
                         "](https://sourceforge.net/projects/lrtwrp-curtana/files/recovery-redmi_note9s-3.4.1-10.0-b4.img/download)Changelog:": "Changelog:",
                         "\n<br>By @": "\n<br>By <a href=https://t.me/",
                         "\n<br>Follow": author
                         }
        for a, b in modifications.items():
            message = message.replace(a, b)
        for line in message.split("\n"):
            for keyword in keywords:
                if f"[{keyword}" in line and message:
                    message = message.replace(
                        f"[{keyword}\n<br>\n<br>](", f"<a href='")
                    message = message.replace(
                        ")Changelog:", f"'>{keyword}</a>\n<br>\n<br>Changelog:")
                    message = message.replace(
                        ")Device changelog:", f"'>{keyword}</a>\n<br>\n<br>Device Changelog:")
        return message

    def parse_data(self):
        data = self.data
        roms = []
        kernels = []
        recoveries = []
        for value in data.values():
            head = f"{value.split()[0][1:]}"
            if "#ROM" in value:
                roms.append(head)
            if "#Kernel" in value:
                kernels.append(head)
            if "#Recovery" in value:
                recoveries.append(head)
        return [roms, kernels, recoveries]

    def save(self, webpage="index", **kwargs):
        path = f"surge/{webpage}/index.html"
        if webpage == "index":
            path = "surge/index.html"
            jinja2_template = str(open(path, "r").read())
        else:
            data = self.data
            text = self.parse_message(data[webpage])
            img = f"<img src=https://curtana.surge.sh/{webpage}/thumbnail.png height='225'>"
            head = f"{text.split()[0]}"
            jinja2_template = "{%extends 'base.html'%}\n{%block title%}\n"\
                + webpage + "\n{%endblock%}\n{%block body%}\n<div class='jumbotron'>"\
                + img + "\n<h1 class='display-4'>\n<hr>\n"\
                + head + "\n</h1>\n"\
                + "<p class='lead'>\n\n"\
                + text[len(head):] + "\n</p>\n<hr>\n</div>\n{%endblock%}"
        template_object = Environment(
            loader=FileSystemLoader("surge")).from_string(jinja2_template)
        static_template = template_object.render(**kwargs)
        with open(path, "w") as f:
            f.write(static_template)

    def refresh(self):
        data = self.parse_data()
        latest = [data[0][0], data[1][0], data[2][0]]
        self.save(roms=sorted(data[0]), kernels=sorted(
            data[1]), recoveries=sorted(data[2]), latest=latest, today=self.today)
