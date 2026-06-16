from django.core.management.base import BaseCommand

from pretix.plugins.sendmail.signals import sendmail_run_rules


class Command(BaseCommand):
    help = "Run scheduled email rules now"

    def handle(self, *args, **options):
        sendmail_run_rules(None)
        self.stdout.write(self.style.SUCCESS('Scheduled email rules executed.'))
