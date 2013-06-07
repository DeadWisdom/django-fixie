from django.core.management.base import BaseCommand, CommandError
from polls.models import Poll

class Command(BaseCommand):
    args = '<path ...>'
    help = 'Runs a transition file.'

    def handle(self, *args, **options):
        for path in args:
            self.stdout.write('Running transition file: %r\n\n' % path)
            execfile(path)
            self.stdout.write('\n\nTransition complete.')