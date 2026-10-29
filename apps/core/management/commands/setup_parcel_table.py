from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from apps.core.models import Parcel


class Command(BaseCommand):
    help = "Create the parcel table without Django migration metadata tables."

    def handle(self, *args, **options):
        connection = connections["default"]
        table = Parcel._meta.db_table
        existing_columns = None

        with connection.cursor() as cursor:
            if table in connection.introspection.table_names(cursor):
                existing_columns = {
                    column.name
                    for column in connection.introspection.get_table_description(cursor, table)
                }
                expected = {field.column for field in Parcel._meta.local_fields}
                unexpected = existing_columns - expected
                if unexpected:
                    raise CommandError(
                        f"{table} exists with unexpected columns: {sorted(unexpected)}"
                    )

        if existing_columns is not None:
            missing_fields = [
                field
                for field in Parcel._meta.local_fields
                if field.column not in existing_columns
            ]
            if missing_fields:
                with connection.schema_editor() as editor:
                    for field in missing_fields:
                        editor.add_field(Parcel, field)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Added parcel columns: {', '.join(field.column for field in missing_fields)}."
                    )
                )
            else:
                self.stdout.write(self.style.SUCCESS(f"{table} table already exists."))
            return

        with connection.schema_editor() as editor:
            editor.create_model(Parcel)
        self.stdout.write(self.style.SUCCESS(f"Created {table} parcel tracking table."))
