import os
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    args = '<path ...>'
    help = 'Runs a transition file.'

    def handle(self, *args, **options):
        for arg in args:
            path = self.find_path(arg)
            self.stdout.write('Running transition file: %r\n\n' % path)
            execfile(path)
            self.stdout.write('\n\nTransition complete.')

    def find_path(self, arg):
        for path in [arg, "transition/%s" % arg, "transition/%s.py" % arg]:
            if os.path.exists(path):
                return path
        raise CommandError("Unnable to find transition: %s - from working directory:" % (arg, os.path.abspath('.')))
