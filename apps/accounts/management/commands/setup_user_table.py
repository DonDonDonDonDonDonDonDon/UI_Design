from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from apps.accounts.models import User


class Command(BaseCommand):
    help = "Create the single user table without Django migration metadata tables."

    def handle(self, *args, **options):
        connection = connections["default"]
        table = User._meta.db_table

        with connection.cursor() as cursor:
            if table in connection.introspection.table_names(cursor):
                columns = {
                    column.name
                    for column in connection.introspection.get_table_description(cursor, table)
                }
                expected = {field.column for field in User._meta.local_fields}
                if columns != expected:
                    raise CommandError(
                        f"{table} exists with unexpected columns: {sorted(columns)}"
                    )
                self.stdout.write(self.style.SUCCESS(f"{table} table already exists."))
                return

        with connection.schema_editor() as editor:
            editor.create_model(User)
        self.stdout.write(self.style.SUCCESS(f"Created {table} with id, password, account, phone."))
