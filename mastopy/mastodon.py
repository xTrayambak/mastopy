import mastodon
import logging

from functools import lru_cache

from mastopy.compute import compute


class Client:
    def __init__(self, api_access_token: str = None, fediverse_url: str = None):
        logging.info(f"Mastodon client API starting")

        self.fediverse_url = fediverse_url
        self.api = mastodon.Mastodon(
            access_token=api_access_token, api_base_url=fediverse_url
        )

        logging.info("Mastodon client API started successfully!")

    def get_notifications(self):
        return self.api.notifications()

    @lru_cache
    @compute
    def get_user(self, id: int) -> dict:
        """
        Get a user's info based on their ID.

        Returns a status dict
        (https://mastodonpy.readthedocs.io/en/stable/02_return_values.html#status-dict)
        """
        return self.api.account(id)

    @compute
    def get_status(self, id):
        return self.api.status(id)

    @compute
    def get_status_context(self, id):
        return self.api.status_context(id)
    @lru_cache
    @compute
    def get_following_list(self, id):
        return self.api.account_following(id)

    @compute
    def follow_user(self, id):
        return self.api.account_follow(id)

    @compute
    def unfollow_user(self, id):
        return self.api.account_unfollow(id)

    @compute
    def make_poll(self, options: list, expires_in, multiple=False, hide_totals=False):
        return self.api.make_poll(options, expires_in, multiple, hide_totals)

    @compute
    def boost_toot(self, id: int):
        return self.api.status_reblog(id)

    @compute
    def revoke_boost_toot(self, id: int):
        return self.api.status_unreblog(id)

    @compute
    def like_toot(self, id: int):
        return self.api.status_favourite(id)

    @compute
    def unlike_toot(self, id: int):
        return self.api.status_unfavourite(id)

    @compute
    def make_toot(self, content: str) -> dict:
        """
        Send a toot via the API.

        Returns a status dict
        (https://mastodonpy.readthedocs.io/en/stable/02_return_values.html#status-dict)
        """
        return self.api.toot(content)

    @lru_cache
    @compute
    def fetch_poll_results(self, id: int) -> dict:
        return self.api.poll(id)

    @compute
    def vote_poll(self, id: int, choices: list) -> dict:
        return self.api.poll_vote(id, choices)

    @lru_cache
    @compute
    def compile_trending_status_list(self) -> dict:
        return self.api.trending_statuses()

    @lru_cache
    @compute
    def compile_local_timeline_list(self) -> dict:
        return self.api.timeline_local()

    @lru_cache
    @compute
    def compile_home_timeline_list(self) -> dict:
        return self.api.timeline_home()

    @lru_cache
    @compute
    def compile_public_timeline_list(self, max_id, remote=False) -> dict:
        return self.api.timeline_public()

    @lru_cache
    @compute
    def compile_trends(self, limit=3):
        # limit set for convenience, as I do not think we will ever use this function past the sidebar
        return self.api.trending_tags(limit)

    @lru_cache
    @compute
    def get_trends(self) -> dict:
        return self.api.trends()

    @lru_cache
    @compute
    def get_self(self):
        return self.api.me()
