"""正式環境設定（部署到 Render / Railway / Fly.io 時使用）。"""

import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403

DEBUG = False

production_secret = os.environ.get("SECRET_KEY", "")
if len(production_secret) < 50 or production_secret.startswith("django-insecure-"):
    raise ImproperlyConfigured("正式環境必須設定至少 50 字元的隨機 SECRET_KEY")

if not os.environ.get("DATABASE_URL"):
    raise ImproperlyConfigured("正式環境必須設定 DATABASE_URL（Neon 連線字串）")

ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("正式環境必須設定 ALLOWED_HOSTS")

CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]

# 反向代理（Render / Fly.io）轉發 https 時需要
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True") == "True"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# 壓縮 + 指紋化靜態檔（需先執行 collectstatic）
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
