"""本機開發設定。"""

from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "0.0.0.0"]

# 若 .env 沒填 SECRET_KEY，沿用 base 的開發用金鑰
