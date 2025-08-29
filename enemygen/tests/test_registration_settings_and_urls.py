import importlib
import types

import pytest
from django.conf import settings as dj_settings
from django.urls import reverse, resolve

from enemygen.reg_views import MyRegistrationView


@pytest.mark.parametrize(
    "setting_name, expected_type",
    [
        ("ACCOUNT_ACTIVATION_DAYS", int),
        ("LOGIN_REDIRECT_URL", str),
        ("LOGIN_URL", str),
    ],
)
def test_required_registration_settings_exist(setting_name, expected_type):
    assert hasattr(dj_settings, setting_name), f"Missing setting: {setting_name}"
    value = getattr(dj_settings, setting_name)
    assert isinstance(value, expected_type), f"{setting_name} should be {expected_type.__name__}"


def test_django_registration_in_installed_apps():
    assert "django_registration" in dj_settings.INSTALLED_APPS


def test_registration_register_url_resolves_to_custom_view():
    # Name defined in enemygen/urls.py
    # NOTE: These tests do not create or authenticate any Django user accounts.
    # They validate URL wiring and view classes only. No specific user is used.
    url = reverse("registration_register")
    assert url.endswith("/accounts/register/")
    match = resolve(url)
    # The view function for class-based views is view_class.as_view(), but resolve provides the wrapper.
    # We can inspect the 'view_class' attribute injected by Django.
    view_func = match.func
    view_class = getattr(view_func, "view_class", None)
    assert view_class is MyRegistrationView


@pytest.mark.parametrize(
    "name",
    [
        # Names provided by django_registration.backends.activation
        "django_registration_register",
        "django_registration_complete",
        "django_registration_disallowed",
        "django_registration_activate",
        "django_registration_activation_complete",
    ],
)
def test_activation_backend_named_urls_are_present(name):
    # Ensure that including activation backend urls succeeded
    # No user is created or referenced here; we only verify that reverse() works for the names.
    if name == "django_registration_activate":
        reverse(name, kwargs={"activation_key": "dummy"})
    else:
        reverse(name)


def test_myregistrationview_success_url():
    # Unit-test the overridden method does not depend on DB
    # Here we deliberately pass a dummy object instead of a real User instance;
    # this test does not rely on any authenticated or created user.
    view = MyRegistrationView()
    # The method signature is get_success_url(self, user)
    dummy_user = object()
    assert view.get_success_url(dummy_user) == "/"
