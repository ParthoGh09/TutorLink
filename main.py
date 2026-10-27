import os
import sys

# PyCharm One-Click Run Script for TutorLink Django Project
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tutorlink.settings')
    from django.core.management import execute_from_command_line
    # Automatically runs the Django development server
    execute_from_command_line(['manage.py', 'runserver'])
