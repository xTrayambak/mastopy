import logging

from mastopy.mastopy_keyring_util import get, set
from mastopy.ui import MastopyApp
from mastopy.mastodon import Client


class Mastopy:
    def __init__(self):
        self.mastopy_app = MastopyApp()

    def run(self):
        self.mastopy_app.run()
