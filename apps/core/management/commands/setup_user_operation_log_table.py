from django.core.management.base import BaseCommand
from django.db import connections

from apps.core.models import UserOperationLog


class Command(BaseCommand):
    help = "Create or update the user operation log table without migration metadata."

    def handle(self, *args, **options):
        connection = connections["default"]
        table = UserOperationLog._meta.db_table

        with connection.cursor() as cursor:
            existing_tables = set(connection.introspection.table_names(cursor))

        if table not in existing_tables:
            with connection.schema_editor() as editor:
                editor.create_model(UserOperationLog)
            self.stdout.write(self.style.SUCCESS(f"Created {table} table."))
            return

        with connection.cursor() as cursor:
            existing_columns = {
                column.name
                for column in connection.introspection.get_table_description(cursor, table)
            }
        missing_fields = [
            field for field in UserOperationLog._meta.local_fields
            if field.column not in existing_columns
        ]
        if missing_fields:
            with connection.schema_editor() as editor:
                for field in missing_fields:
                    editor.add_field(UserOperationLog, field)
            self.stdout.write(self.style.SUCCESS(
                f"Added operation log columns: {', '.join(field.column for field in missing_fields)}."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(f"{table} table already exists."))
