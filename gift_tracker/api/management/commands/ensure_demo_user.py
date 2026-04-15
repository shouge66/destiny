from django.core.management.base import BaseCommand

from api.views import ensure_demo_user


class Command(BaseCommand):
    help = "Create or refresh the configured demo user."

    def handle(self, *args, **options):
        user = ensure_demo_user()
        self.stdout.write(self.style.SUCCESS(f"Demo user ready: {user.username}"))