import pytest
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_can_create_basic_user_with_password(localtest_username):
    """
    This test explicitly creates a Django auth user using the built-in User model.
    We verify that:
    - The user record is stored in the database
    - The password is hashed and check_password works
    - The user is active by default (standard Django behavior for create_user)

    User used in this test (generated uniquely per run):
      username = localtest-<random>
      email    = "localtest@example.com"
      password = "S3cretPass!"
    """
    User = get_user_model()

    username = localtest_username  # comes from conftest.py fixture, always starts with "localtest-"
    email = "localtest@example.com"
    raw_password = "S3cretPass!"

    user = User.objects.create_user(username=username, email=email, password=raw_password)

    # Fetch again to ensure it is persisted
    fetched = User.objects.get(username=username)

    assert fetched.id is not None
    assert fetched.username == username
    assert fetched.email == email
    assert fetched.is_active is True

    # Password should be hashed; direct equality should fail, but check_password must pass
    assert fetched.password != raw_password
    assert fetched.check_password(raw_password)
