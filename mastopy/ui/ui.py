import re

from threading import Thread

import regex
from bs4 import BeautifulSoup
from time import sleep

from kivy.loader import Loader
from kivy.lang.builder import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import mainthread, Clock
from kivy.properties import StringProperty
from kivy.uix.screenmanager import ScreenManager

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from mastopy import mastodon
from mastopy.mastopy_keyring_util import get
from kivy.uix.label import Label
from mastopy.utils import detect_hashtags_in_post
from kivy.uix.behaviors import ButtonBehavior


# create the screen controller.
sm = ScreenManager()
client = None
feed_updating=False
focused_post = ""


class PostView(ButtonBehavior, BoxLayout):

    # declares the view that posts will be shown in.
    def like_toot(a, id, liked):
        if not liked:
            a.ids["'like_counter'"].text = str(
                int(a.ids["'like_counter'"].text) + 1)
            a.ids["star_post"].icon = "star"
            client.like_toot(id)
            return True
        else:
            a.ids["'like_counter'"].text = str(
                int(a.ids["'like_counter'"].text) - 1)
            a.ids["star_post"].icon = "star-outline"
            client.unlike_toot(id)
            return False

    def boost_toot(a, id, boosted):
        if not boosted:
            a.ids["boost_post"].icon = "swap-horizontal-variant"
            client.boost_toot(id)
            return True
        else:
            a.ids["boost_post"].icon = "swap-horizontal-circle-outline"
            client.revoke_boost_toot(id)
            return False

    def follow_account(a, id, following):
        if not following:
            a.ids["follow_button"].icon = "account"
            client.follow_user(id)
            return True
        else:
            a.ids["follow_button"].icon = "account-plus-outline"
            client.unfollow_user(id)
            return False
        # these return values change the liked value without having to access its id.

    # these values cannot be properties otherwise all values on screen will be equal.

    med_size = "128dp"
    id = "pview"
    text = ""
    username = ""
    usertag = ""
    icon_source = ""
    attachment_image = ""
    liked = ""
    liked_icon = ""
    boosted = ""
    boosted_icon = ""
    following = ""
    following_icon = "account-plus-outline"
    account = ""

    favourites_count = StringProperty(0)

    # logic to determine icon of post

class NotificationScreen(MDScreen):
    pass

class OpenedPost(MDScreen):
    def on_pre_enter(self, *args):
        opened_ids = sm.get_screen("openpost").ids
        opened_ids.reply_holder.clear_widgets()
        opened_ids.post_holder.clear_widgets()
        MastopyApp.change_feed(
            MastopyApp,
            feed=client.get_status(focused_post),
            container=opened_ids.post_holder,
            row=False,
        )
        MastopyApp.change_feed(
            MastopyApp,
            feed=client.get_status_context(focused_post)["descendants"],
            container=opened_ids.reply_holder,
        )


class Home(MDScreen):
    # declares the home screen shown after login.
    queued_posts=[]
    last_post=0
    def handle_scroll(self):
        global feed_updating
        if self.ids.scroll_post.scroll_y<.6 and feed_updating!=True:
            feed_updating=True
            def add_posts():
                global feed_updating
                print('updating...')
                if self.ids.bar.feed_type == "earth":
                    
                    feed = client.compile_public_timeline_list(self, max_id=self.last_post)
                    self.last_post = str(next(reversed(feed))['id'])
                    self.queued_posts.extend(feed)
                    #returns the last post of the containers children and tells the function to place the widget after that
                    for post in self.queued_posts:
                        #pop out posts time to time to keep the timeline fresh without lagging the mainthread.
                        Clock.schedule_once(lambda x: MastopyApp.change_feed(MastopyApp, self.queued_posts.pop(0), self.ids.post_container, False, 0))
                        #clock.schedule has its own timer method, but its not the same. it tells the clock to schedule each instruction right after telling the last one in the for loop.
                        #it happens so quick that when the time actually comes all the widgets are expected to be added in a vicinity of.1 seconds.
                        sleep(1)
                    sleep(5)
                    feed_updating=False
            Thread(target=add_posts).start()

        #sends too many requests and spams mastodon, also blocks ui thread. Please fix!

class Login(MDScreen):
    # declares the login widget so elements are accessible from python.
    pass


class MastopyApp(MDApp):
    link_regex_https = r"(https?://\S+)"
    link_regex_http = r"(http?://\S+)"

    focus = None
    home_ids = None
    feed = None
    user_account = None
    client = None
    following_list = []
    feed_name = StringProperty("explore")
    feed_type = StringProperty("magnify")

    since_post = 0

    def build(self):
        if get("mastopy_firstrun") != "1":
            self.firstrun()
            return sm
        else:
            Loader.loading_image = "mastopy/assets/gif/async_load.gif"
            self.client = mastodon.Client(
                get("mastopy_access_token"), get("mastopy_fediverse_url")
            )
            global client
            client = self.client
            self.user_account = self.client.get_self()
            self.following_list = self.client.get_following_list(
                self.user_account["id"]
            )

            self.home_screen()
            # screen manager opens the first widget added to it. SO sm has to add the opened post after home screen
            sm.add_widget(OpenedPost(name="openpost"))
            return sm

    def firstrun(self):
        Builder.load_file("mastopy/ui/creds.kv").__dir__()
        sm.add_widget(Login(name="login"))
        return sm

    def home_screen(self):
        Builder.load_file("mastopy/ui/home.kv")
        sm.add_widget(Home(name="home"))
        self.get_feed()

    def open_post(self, post):
        global focused_post
        focused_post = post
        sm.current = "openpost"

    def go_home(self):
        sm.current = "home"

    def find_all_emojis(self, string):
        emoji_pattern = re.compile(
            "["
            "\U0001f600-\U0001f64f"  # emoticons
            "\U0001f300-\U0001f5ff"  # symbols & pictographs
            "\U0001f680-\U0001f6ff"  # transport & map symbols
            "\U0001f1e0-\U0001f1ff"  # flags (iOS)
            "]+",
            flags=re.UNICODE,
        )
        emojis = emoji_pattern.findall(string)
        return emojis

    def get_feed(self):
        self.feed = self.client.compile_trending_status_list()
        self.update_feed(self.feed)

    def switch_feed(self, feedicon):
        self.home_ids.post_container.clear_widgets()
        if feedicon == "home":
            self.feed_type = "magnify"
            self.feed_name = "explore"

            def switch():
                feed=client.compile_trending_status_list()
                Home.last_post = str(next(reversed(feed))['id'])
                self.fetch_feed(feed)
            Thread(target=switch).start()
        elif feedicon == "magnify":
            self.feed_type = "earth"
            self.feed_name = "public"

            def switch():
                feed=client.compile_public_timeline_list(self)
                Home.last_post = str(next(reversed(feed))['id'])
                self.fetch_feed(feed)
                #str(next(reversed(feed))['id'])
            Thread(target=switch).start()

        elif feedicon == "earth":
            self.feed_type = "account-group"
            self.feed_name = "local"

            def switch():
                feed=client.compile_local_timeline_list()
                Home.last_post = str(next(reversed(feed))['id'])
                self.fetch_feed(feed)
            Thread(target=switch).start()

        else:
            # runs if we are on local.
            self.feed_type = "home"
            self.feed_name = "home"

            def switch():
                feed=client.compile_home_timeline_list()
                Home.last_post = str(next(reversed(feed))['id'])
                self.fetch_feed(feed)
            Thread(target=switch).start()


    def fetch_feed(self, feed_type):
        feed = feed_type
        self.update_feed(feed)

    def dispatch_url_in_post(self, pview: PostView):
        urls = [
            *regex.findall(self.link_regex_http, pview.text),
            *regex.findall(self.link_regex_https, pview.text),
        ]

        if len(urls) != 0:
            for url in urls:
                if url.startswith("https"):
                    PostView.text = PostView.text.replace(
                        url, f"[color=#0000EE][ref={url}] {url} [/ref][/color]"
                    )
                else:
                    PostView.text = PostView.text.replace(
                        url, f"[color=#FF0000][ref={url}] {url} [/ref][/color]"
                    )

    def change_feed(self, feed, container, row=True, index=1):
        if row:
            for post in feed:
                replied_to = post["in_reply_to_account_id"]
                user_raw_url = post["account"]["url"].split("https://")[1]
                user_fediverse_url = user_raw_url.split("/")
                user_tag = f"{user_fediverse_url[1]}@{user_fediverse_url[0]}"
                html_post_text = BeautifulSoup(post["content"], "lxml")
                attachments = post["media_attachments"]

                PostView.id = post["id"]
                PostView.text = html_post_text.get_text()
                PostView.username = post["account"]["username"]
                PostView.icon_source = post["account"]["avatar_static"]
                PostView.usertag = user_tag
                PostView.attachment_image = ""
                PostView.favourites_count = post["favourites_count"]
                PostView.liked = ""
                PostView.account = post["account"]
                PostView.following = ""
                PostView.following_icon = "account-plus-outline"

                MastopyApp.dispatch_url_in_post(self, PostView)
                emojis = MastopyApp.find_all_emojis(self, PostView.text)
                #hashtags = detect_hashtags_in_post(PostView.text, True)
                #line 285def update
                #for hashtag in hashtags:
                    #PostView.text = PostView.text.replace(hashtag, f"[color=#0000EE]{hashtag}[/color]")

                if post["favourited"]:
                    PostView.liked = True
                    PostView.liked_icon = "star"
                else:
                    PostView.liked = False
                    PostView.liked_icon = "star-outline"

                if post["reblogged"]:
                    PostView.boosted_icon = "swap-horizontal-variant"
                    PostView.boosted = True
                else:
                    PostView.boosted_icon = "swap-horizontal-circle-outline"
                    PostView.boosted = False

                for attachment in attachments:
                    if attachment["type"] == "image":
                        PostView.attachment_image = attachment["url"]

                for follower in self.following_list:
                    if int(PostView.account["id"]) == follower["id"]:
                        PostView.following = True
                        PostView.following_icon = "account"
                        break

                if PostView.attachment_image == "":
                    PostView.med_size = "0dp"
                else:
                    PostView.med_size = "128dp"
                @mainthread
                def update(post, index):
                    container.add_widget(post, index=index)
                Thread(target=update, args=(PostView(), index)).start()
        else:
            PostView.style = "outlined"
            replied_to = feed["in_reply_to_account_id"]
            user_raw_url = feed["account"]["url"].split("https://")[1]
            user_fediverse_url = user_raw_url.split("/")
            user_tag = f"{user_fediverse_url[1]}@{user_fediverse_url[0]}"
            html_post_text = BeautifulSoup(feed["content"], "lxml")
            attachments = feed["media_attachments"]

            PostView.id = feed["id"]
            PostView.text = html_post_text.get_text()
            PostView.username = feed["account"]["username"]
            PostView.icon_source = feed["account"]["avatar_static"]
            PostView.usertag = user_tag
            PostView.attachment_image = ""
            PostView.favourites_count = feed["favourites_count"]
            PostView.liked = ""
            PostView.account = feed["account"]
            PostView.following = ""
            PostView.following_icon = "account-plus-outline"

            MastopyApp.dispatch_url_in_post(self, PostView)
            emojis = MastopyApp.find_all_emojis(self, PostView.text)

            for emoji in emojis:
                PostView.text = PostView.text.replace(
                    emoji,
                    f"[font=mastopy/assets/fonts/Twemoji.Mozilla.ttf]{emoji}[/font]",
                )

            if feed["favourited"]:
                PostView.liked = True
                PostView.liked_icon = "star"
            else:
                PostView.liked = False
                PostView.liked_icon = "star-outline"

            if feed["reblogged"]:
                PostView.boosted_icon = "swap-horizontal-variant"
                PostView.boosted = True
            else:
                PostView.boosted_icon = "swap-horizontal-circle-outline"
                PostView.boosted = False

            for attachment in attachments:
                if attachment["type"] == "image":
                    PostView.attachment_image = attachment["url"]

            for follower in self.following_list:
                if int(PostView.account["id"]) == follower["id"]:
                    PostView.following = True
                    PostView.following_icon = "account"
                    break

            if PostView.attachment_image == "":
                PostView.med_size = "0dp"
            else:
                PostView.med_size = "128dp"
            container.add_widget(PostView())

    @mainthread
    def update_feed(self, feed, first_update=True, index=1):
        self.home_ids = sm.get_screen("home").ids
        MastopyApp.change_feed(self=MastopyApp, feed=feed, container=self.home_ids.post_container, index=index)
        #this is done in case the method is run when switching to an empty feed. 
        #without this instruction the scrollview starts from the bottom and goes up.
        if first_update:
            self.home_ids.scroll_post.scroll_y = 1
