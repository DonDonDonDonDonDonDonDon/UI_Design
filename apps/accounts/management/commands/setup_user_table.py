import random

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.models import Q

from apps.accounts.models import User


class Command(BaseCommand):
    help = "Create or update the user table without Django migration metadata tables."

    SAMPLE_NAMES = (
        "林小晴", "陳柏宇", "黃品妍", "張家豪", "李雨彤", "王冠廷",
        "吳佳蓉", "劉承恩", "蔡宜庭", "楊子謙", "許雅涵", "鄭宇翔",
    )
    SAMPLE_GROUPS = ("第一組", "第二組", "第三組", "第四組")

    def handle(self, *args, **options):
        connection = connections["default"]
        table = User._meta.db_table

        with connection.cursor() as cursor:
            tables = set(connection.introspection.table_names(cursor))

        if table not in tables:
            with connection.schema_editor() as editor:
                editor.create_model(User)
            self.stdout.write(self.style.SUCCESS(f"Created {table} user table."))
        else:
            with connection.cursor() as cursor:
                columns = {
                    column.name
                    for column in connection.introspection.get_table_description(cursor, table)
                }
            missing_fields = [
                field for field in User._meta.local_fields
                if field.column not in columns
            ]
            if missing_fields:
                with connection.schema_editor() as editor:
                    for field in missing_fields:
                        editor.add_field(User, field)
                self.stdout.write(self.style.SUCCESS(
                    f"Added user columns: {', '.join(field.column for field in missing_fields)}."
                ))

        rng = random.SystemRandom()
        updated = 0
        members_needing_samples = User.objects.exclude(account="Manager").filter(
            Q(name="") | Q(group_name="")
        )
        for user in members_needing_samples:
            if not user.name:
                user.name = rng.choice(self.SAMPLE_NAMES)
            if not user.group_name:
                user.group_name = rng.choice(self.SAMPLE_GROUPS)
            user.save(update_fields=("name", "group_name"))
            updated += 1
        self.stdout.write(self.style.SUCCESS(
            f"Assigned sample names and groups to {updated} existing members."
        ))
