# Initial parcel tracking schema.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("accounts", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="Parcel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tracking_number", models.CharField(max_length=32, unique=True, verbose_name="郵件單號")),
                ("package_type", models.CharField(choices=[("letter", "信件 / 小包"), ("registered", "掛號郵件"), ("box", "便利箱"), ("bag", "便利袋"), ("international", "國際包裹")], max_length=20, verbose_name="包裹種類")),
                ("origin_office", models.CharField(default="臺北北門郵局", max_length=120, verbose_name="寄件郵局")),
                ("destination_office", models.CharField(default="臺北大安郵局", max_length=120, verbose_name="收件郵局")),
                ("current_status", models.CharField(choices=[("accepted", "已收寄"), ("in_transit", "運送中"), ("out_for_delivery", "配送中"), ("delivered", "已送達"), ("exception", "配送異常")], default="accepted", max_length=24, verbose_name="目前狀態")),
                ("current_location", models.CharField(default="郵局收寄", max_length=120, verbose_name="目前位置")),
                ("route_stops", models.JSONField(blank=True, default=list, verbose_name="運送站點")),
                ("sent_at", models.DateTimeField(auto_now_add=True, verbose_name="寄件時間")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="進度更新時間")),
                ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="received_parcels", to=settings.AUTH_USER_MODEL, verbose_name="收件人")),
                ("sender", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sent_parcels", to=settings.AUTH_USER_MODEL, verbose_name="寄件人")),
            ],
            options={"db_table": "parcel", "ordering": ("-updated_at",), "verbose_name": "包裹", "verbose_name_plural": "包裹"},
        ),
    ]
