from cryptokings.settings import TELEGRAM_ID, TELEGRAM_HASH
from telethon.sync import TelegramClient
import logging
from cryptokings.settings import TELEGRAM_GROUP_LINK
import logging

class Handler:
    __instance__ = None

    def __init__(self):
        self.bot = TelegramClient('bot', TELEGRAM_ID, TELEGRAM_HASH)
        self.bot.start()
        self.entity = self.bot.get_entity(TELEGRAM_GROUP_LINK)

    @staticmethod
    def get_instance():
        if not Handler.__instance__:
            Handler.__instance__ = Handler()
            return Handler.__instance__
        else:
            return Handler.__instance__

    def send_message(self, contact, message):
        logging.info("Sending message")
        try:
            self.bot.send_message(contact, message)
        except:
            logging.error(exc_info=True)

    def send_all_subscribers(self, message):
        if message == "" or message is None:
            return
        self.send_message(self.entity, message)

