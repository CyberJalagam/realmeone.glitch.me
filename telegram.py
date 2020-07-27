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
from util import command
import os


class ReverseList(list):
    def __iter__(self):
        return reversed(self)


class Userbot(TelegramClient):
    def __init__(self, session, *, plugin_path="plugins", storage=None, bot_token=None, api_config=None, **kwargs):
        self._name = "LoggedIn"
        self._logger = logging.getLogger("Telegram")
        self._plugins = {}
        self._plugin_path = plugin_path
        self.config = api_config

        kwargs = {
            "api_id": 6,
            "api_hash": "eb06d4abfb49dc3eeb1aeb98ae0f581e",
            "device_model": "GNU/Linux nonUI",
            "app_version": "@The_TG_Bot 3.0",
            "lang_code": "en",
            **kwargs
        }

        self.tgbot = None
        super().__init__(session, **kwargs)
        self._event_builders = ReverseList()
        self.loop.run_until_complete(self._async_init(bot_token=bot_token))

        core_plugin = Path(__file__).parent / "watcher.py"
        self.load_plugin_from_file(core_plugin)

        for a_plugin_path in Path().glob(f"{self._plugin_path}/*.py"):
            self.load_plugin_from_file(a_plugin_path)

        LOAD = self.config.LOAD
        NO_LOAD = self.config.NO_LOAD
        if LOAD or NO_LOAD:
            to_load = LOAD
            if to_load:
                self._logger.info("Modules to LOAD: ")
                self._logger.info(to_load)
            if NO_LOAD:
                for plugin_name in NO_LOAD:
                    if plugin_name in self._plugins:
                        self.remove_plugin(plugin_name)

    async def _async_init(self, **kwargs):
        await self.start(**kwargs)

        self.me = await self.get_me()
        self.uid = telethon.utils.get_peer_id(self.me)

        self._logger.info(f"Logged in as {self.uid}")

    def load_plugin(self, shortname):
        self.load_plugin_from_file(f"{self._plugin_path}/{shortname}.py")

    def load_plugin_from_file(self, path):
        path = Path(path)
        shortname = path.stem
        name = f"_UserbotPlugins.{self._name}.{shortname}"
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        mod.command = command
        mod.bot = self
        mod.logger = logging.getLogger(shortname)
        mod.Config = self.config
        spec.loader.exec_module(mod)
        self._plugins[shortname] = mod
        self._logger.info(f"Successfully loaded {shortname}")

    def remove_plugin(self, shortname):
        name = self._plugins[shortname].__name__

        for i in reversed(range(len(self._event_builders))):
            ev, cb = self._event_builders[i]
            if cb.__module__ == name:
                del self._event_builders[i]

        del self._plugins[shortname]
        self._logger.info(f"Removed plugin {shortname}")

    def await_event(self, event_matcher, filter=None):
        fut = asyncio.Future()

        @self.on(event_matcher)
        async def cb(event):
            try:
                if filter is None or await filter(event):
                    fut.set_result(event)
            except telethon.events.StopPropagation:
                fut.set_result(event)
                raise

        fut.add_done_callback(
            lambda _: self.remove_event_handler(cb, event_matcher))

        return fut
