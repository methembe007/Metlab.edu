from django.core.management.base import BaseCommand
from django.core.management import call_command
from community.models import Subject


class Command(BaseCommand):
    help = 'Initialize the tutoring system with subjects and sample data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Initializing tutoring system...'))
        
        # Load initial subjects if they don't exist
        if not Subject.objects.exists():
            self.stdout.write('Loading initial subjects...')
            call_command('loaddata', 'community/fixtures/initial_subjects.json')
            self.stdout.write(self.style.SUCCESS('✓ Subjects loaded successfully'))
        else:
            self.stdout.write('✓ Subjects already exist')
        
        # Display summary
        subject_count = Subject.objects.count()
        self.stdout.write(f'✓ Total subjects available: {subject_count}')
        
        self.stdout.write(self.style.SUCCESS('Tutoring system initialization complete!'))
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('1. Create tutor profiles through the admin interface')
        self.stdout.write('2. Set up tutor availability schedules')
        self.stdout.write('3. Students can now search and book tutors')