import os


class ENV(object):
    LOGGER = True
    MAX_MESSAGE_SIZE_LIMIT = 4095  # TG API Limit
    LOAD = []
    NO_LOAD = []
    DB_URI = os.environ.get("DATABASE_URL", None)
    APP_ID = int(os.environ.get("APP_ID", 1))
    API_HASH = str(os.environ.get("API_HASH", "None"))
    SESSION = os.environ.get("SESSION", None)
    LOGGER_GROUP = int(os.environ.get(
        "LOGGER_GROUP", 0))
    DOWNLOAD_DIRECTORY = os.environ.get(
        "DOWNLOAD_DIRECTORY", "./DOWNLOADS/")
    COMMAND_HANDLER = os.environ.get("COMMAND_HANDLER", "\/")
    SUDO_USERS = os.environ.get("SUDO_USERS", "").split()
    CHATS = os.environ.get("CHATS", "").split()
    FILTERS = os.environ.get("FILTERS", "").split()
    BLOCKED = os.environ.get("BLOCKED", "").split()
    GLITCH_GIT_URL = os.environ.get("GLITCH_GIT_URL", None)
    # Get app name from git url automatically
    GLITCH_APP = GLITCH_GIT_URL.split("/")[-1]


class _ENV(ENV):
    pass
    # Add values here to use for development
