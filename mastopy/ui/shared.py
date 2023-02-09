from kivy.properties import StringProperty, NumericProperty


class States:
    KEYRING_UNLOCK = NumericProperty(0)
    CREDS = NumericProperty(1)
    FEED = NumericProperty(2)
    PROFILE = NumericProperty(3)
    SETTINGS = NumericProperty(4)
