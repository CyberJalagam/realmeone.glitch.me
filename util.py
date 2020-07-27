# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re
import math
import os
import time
from telethon import events
from telethon.tl.functions.messages import GetPeerDialogsRequest


ENV = bool(os.environ.get("ENV", False))
if ENV:
    from production import Config
else:
    if os.path.exists("development.py"):
        from development import Config


def command(pattern=None, incoming=False, func=None, **args):
    """
    Simpler function to handle events without having to import telethon.events
    also enables command_handler functionality
    """
    args["func"] = lambda e: e.via_bot_id is None
    if func is not None:
        args["func"] = func
    if pattern is not None:
        args["pattern"] = re.compile("." + pattern)
    if incoming:
        args["incoming"] = True
    else:
        args["outgoing"] = True
    return events.NewMessage(**args)
