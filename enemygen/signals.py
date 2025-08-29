from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model


@receiver(post_migrate)
def ensure_manualuser(sender, **kwargs):
    """
    Ensure a manual testing user exists for interactive login:
    - username: manualuser
    - password: spade1
    Runs after migrations for any app; idempotent and fail-soft.
    """
    try:
        User = get_user_model()
        # Ensure the auth tables exist by attempting a simple query
        # If the DB is not available yet, just return silently.
        # Create/update the user
        user, _created = User.objects.get_or_create(
            username="manualuser",
            defaults={
                "email": "manualuser@example.com",
                "is_active": True,
            },
        )
        # Always ensure active and password set to the known value
        updated = False
        if not user.is_active:
            user.is_active = True
            updated = True
        # Set password every time to ensure it matches expected value
        user.set_password("spade1")
        updated = True
        if updated:
            user.save()
    except Exception:
        # Never block app startup if anything goes wrong here
        return
