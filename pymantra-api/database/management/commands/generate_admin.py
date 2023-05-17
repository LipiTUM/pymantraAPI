from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings


class Command(BaseCommand):
    help = """Generate a superuser.
    
    Note that if any argument is passed, it is expected that none of the 
    defaults specified by the .env file are used, hence 'username', 'email'
    and 'password' all need to be given.
    """

    def add_arguments(self, parser):
        parser.add_argument('--username', help="Admin's username")
        parser.add_argument('--email', help="Admin's email")
        parser.add_argument('--password', help="Admin's password")

    def handle(self, *args, **options):
        user = get_user_model()

        username = options['username']
        password = options['password']
        email = options['email']
        isnone = [x is None for x in [username, password, email]]
        if all(isnone):
            username = settings.DJANGO_ADMIN.get('user', 'admin')
            password = settings.DJANGO_ADMIN.get('password', '123')
            email = settings.DJANGO_ADMIN.get('email', 'nomail@test.com')
        elif any(isnone):
            raise ValueError(
                "Missing argument. Note that if any argument is passed, "
                "it is expected that none of the defaults specified by "
                "the .env file are used, hence 'username', 'email' "
                "and 'password' all need to be given."
            )

        if not user.objects.filter(username=username).exists():
            user.objects.create_superuser(
                username=username, email=email, password=password)
            print("Successfully created new superuser")
