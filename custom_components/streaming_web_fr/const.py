from __future__ import annotations

DOMAIN = "streaming_web_fr"
NAME = "Streaming Web FR"
VERSION = "0.6.0-beta.5"

CONF_PROVIDERS = "providers"
CONF_PLAYERS = "players"

DEFAULT_PROVIDER_TYPE = "drabam"
SUPPORTED_PROVIDER_TYPES = ("drabam",)

AUTH_NONE = "none"
AUTH_BASIC = "basic"
AUTH_FORM_LOGIN = "form_login"
AUTH_API_KEY = "api_key"
AUTH_BEARER = "bearer"
AUTH_COOKIE = "cookie"
AUTH_CUSTOM_HEADERS = "custom_headers"

AUTH_MODES = (
    AUTH_NONE,
    AUTH_BASIC,
    AUTH_FORM_LOGIN,
    AUTH_API_KEY,
    AUTH_BEARER,
    AUTH_COOKIE,
    AUTH_CUSTOM_HEADERS,
)

VLC_ANDROID_PACKAGE = "org.videolan.vlc"
VLC_ANDROID_ACTIVITY = "org.videolan.vlc/.StartActivity"

CARD_RESOURCE_PATH = "/streaming_web_fr/streaming-web-fr-card.js"
