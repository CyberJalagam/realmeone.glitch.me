# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import importlib.util
import logging
from pathlib import Path
from telethon import TelegramClient
import telethon.utils
import telethon.events
from datetime import datetime
from production import Config
from util import register, humanbytes, progress, time_formatter
import os


class Reverse(list):
    def __iter__(self):
        return reversed(self)


class Userbot(TelegramClient):
    def __init__(
            self, session, *, module_path="modules", storage=None,
            bot_token=None, api_config=None, **kwargs):
        self._name = "The-TG-Bot-v3"
        self.storage = storage or (lambda n: Storage(Path("data") / n))
        self._logger = logging.getLogger("Userbot")
        self._modules = {}
        self._module_path = module_path
        self.config = api_config

        kwargs = {
            "api_id": 6,
            "api_hash": "eb06d4abfb49dc3eeb1aeb98ae0f581e",
            "device_model": "Website",
            "app_version": f"@{Config.SUBDOMAIN}.surge.sh",
            "lang_code": "en",
            **kwargs
        }

        self.tgbot = None
        super().__init__(session, **kwargs)
        self._event_builders = Reverse()
        self.loop.run_until_complete(self._async_init(bot_token=bot_token))
        core_module = Path(__file__).parent / "app.py"
        self.load_module_from_file(core_module)

        for a_module_path in Path().glob(f"{self._module_path}/*.py"):
            self.load_module_from_file(a_module_path)

        LOAD = self.config.LOAD
        NO_LOAD = self.config.NO_LOAD
        if LOAD or NO_LOAD:
            to_load = LOAD
            if to_load:
                self._logger.info("Modules to LOAD: ")
                self._logger.info(to_load)
            if NO_LOAD:
                for module_name in NO_LOAD:
                    if module_name in self._modules:
                        self.remove_module(module_name)

    async def _async_init(self, **kwargs):
        await self.start(**kwargs)
        self.me = await self.get_me()
        self.uid = telethon.utils.get_peer_id(self.me)
        self._logger.info(f"Logged in as {self.uid}")

    def load_module(self, shortname):
        self.load_module_from_file(f"{self._module_path}/{shortname}.py")

    def load_module_from_file(self, path):
        path = Path(path)
        shortname = path.stem
        name = f"_UserbotModules.{self._name}.{shortname}"
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        mod.register = register
        mod.client = self
        mod.humanbytes = humanbytes
        mod.progress = progress
        mod.time_formatter = time_formatter
        mod.logger = logging.getLogger(shortname)
        mod.Config = self.config
        spec.loader.exec_module(mod)
        self._modules[shortname] = mod
        self._logger.info(f"Successfully loaded module {shortname}")

    def remove_module(self, shortname):
        name = self._modules[shortname].__name__

        for i in reversed(range(len(self._event_builders))):
            ev, cb = self._event_builders[i]
            if cb.__module__ == name:
                del self._event_builders[i]

        del self._modules[shortname]
        self._logger.info(f"Removed module {shortname}")

    def await_event(self, event_matcher, filter=None):
        future = asyncio.Future()

        @self.on(event_matcher)
        async def callback(event):
            try:
                if filter is None or await filter(event):
                    future.set_result(event)
            except telethon.events.StopPropagation:
                future.set_result(event)
                raise

        future.add_done_callback(
            lambda _: self.remove_event_handler(callback, event_matcher))

        return future
