# Initial schema for the single-table account setup.
import apps.accounts.models
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("account", models.CharField(max_length=150, unique=True, verbose_name="帳號")),
                ("phone", models.CharField(max_length=20, verbose_name="電話")),
            ],
            options={"db_table": "user", "verbose_name": "會員", "verbose_name_plural": "會員"},
            managers=[("objects", apps.accounts.models.UserManager())],
        ),
    ]
