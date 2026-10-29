from django.core.management.base import BaseCommand, CommandError

from apps.core.models import RemittanceQueue


class Command(BaseCommand):
    help = "Update the current waiting count for a post office."

    def add_arguments(self, parser):
        parser.add_argument("office_name", help="郵局名稱")
        parser.add_argument("waiting_people", type=int, help="目前等候人數")

    def handle(self, *args, **options):
        waiting_people = options["waiting_people"]
        if waiting_people < 0:
            raise CommandError("等候人數不可小於 0。")

        queue, created = RemittanceQueue.objects.update_or_create(
            office_name=options["office_name"],
            defaults={"waiting_people": waiting_people},
        )
        action = "新增" if created else "更新"
        self.stdout.write(self.style.SUCCESS(
            f"{action}{queue.office_name}等候人數：{queue.waiting_people} 人。"
        ))
