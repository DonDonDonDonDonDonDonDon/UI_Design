from django.core.management.base import BaseCommand
from django.db import connections
from django.db import models
from django.db.models import F

from apps.core.models import RemittanceQueue, RemittanceTicket


INITIAL_WAITING_COUNTS = {
    "臺北北門郵局": 8,
    "臺北大安郵局": 14,
    "新北板橋郵局": 3,
    "臺中民權路郵局": 6,
}


class Command(BaseCommand):
    help = "Create and initialize the remittance queue table without Django migration metadata."

    def handle(self, *args, **options):
        connection = connections["default"]
        table = RemittanceQueue._meta.db_table
        ticket_table = RemittanceTicket._meta.db_table

        with connection.cursor() as cursor:
            existing_tables = set(connection.introspection.table_names(cursor))

        if table not in existing_tables:
            with connection.schema_editor() as editor:
                editor.create_model(RemittanceQueue)
            self.stdout.write(self.style.SUCCESS(f"Created {table} table."))
        else:
            with connection.cursor() as cursor:
                existing_columns = {
                    column.name
                    for column in connection.introspection.get_table_description(cursor, table)
                }
            missing_fields = [
                field for field in RemittanceQueue._meta.local_fields
                if field.column not in existing_columns
            ]
            if missing_fields:
                with connection.schema_editor() as editor:
                    for field in missing_fields:
                        editor.add_field(RemittanceQueue, field)
                if any(field.name == "last_ticket_number" for field in missing_fields):
                    RemittanceQueue.objects.update(last_ticket_number=F("waiting_people"))
                self.stdout.write(self.style.SUCCESS(
                    f"Added remittance queue columns: {', '.join(field.column for field in missing_fields)}."
                ))

        if ticket_table not in existing_tables:
            with connection.schema_editor() as editor:
                editor.create_model(RemittanceTicket)
            self.stdout.write(self.style.SUCCESS(f"Created {ticket_table} table."))
        else:
            with connection.cursor() as cursor:
                existing_columns = {
                    column.name
                    for column in connection.introspection.get_table_description(cursor, ticket_table)
                }
                constraints = connection.introspection.get_constraints(cursor, ticket_table)
            missing_fields = [
                field for field in RemittanceTicket._meta.local_fields
                if field.column not in existing_columns
            ]
            if missing_fields:
                with connection.schema_editor() as editor:
                    for field in missing_fields:
                        editor.add_field(RemittanceTicket, field)
                self.stdout.write(self.style.SUCCESS(
                    f"Added ticket columns: {', '.join(field.column for field in missing_fields)}."
                ))

            old_constraint_name = "unique_user_remittance_ticket_per_office"
            new_constraint = next(
                constraint for constraint in RemittanceTicket._meta.constraints
                if constraint.name == "unique_user_ticket_per_office_business"
            )
            with connection.schema_editor() as editor:
                if old_constraint_name in constraints:
                    editor.remove_constraint(
                        RemittanceTicket,
                        models.UniqueConstraint(
                            fields=("user", "office_name"), name=old_constraint_name
                        ),
                    )
                    self.stdout.write(self.style.SUCCESS("Updated ticket uniqueness to include business type."))
                if new_constraint.name not in constraints:
                    editor.add_constraint(RemittanceTicket, new_constraint)

        for office_name, waiting_people in INITIAL_WAITING_COUNTS.items():
            RemittanceQueue.objects.get_or_create(
                office_name=office_name,
                defaults={
                    "waiting_people": waiting_people,
                    "last_ticket_number": waiting_people,
                },
            )

        self.stdout.write(self.style.SUCCESS("Initialized missing remittance queue records."))
