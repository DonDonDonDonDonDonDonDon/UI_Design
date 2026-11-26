from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, account):
        return self.get(account=account)

    def create_user(self, account, phone, password=None, name="", group_name=""):
        if not account:
            raise ValueError("帳號不可為空")
        user = self.model(
            account=account, phone=phone, name=name, group_name=group_name
        )
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    """登入會員資料。"""

    last_login = None
    account = models.CharField("帳號", max_length=150, unique=True)
    phone = models.CharField("電話", max_length=20)
    name = models.CharField("名字", max_length=80, default="", blank=True)
    group_name = models.CharField(
        "組別", max_length=80, default="", blank=True, db_column="group"
    )

    objects = UserManager()

    USERNAME_FIELD = "account"
    REQUIRED_FIELDS = []

    @property
    def is_active(self):
        return True

    @property
    def is_staff(self):
        return False

    class Meta:
        db_table = "user"
        verbose_name = "會員"
        verbose_name_plural = "會員"
