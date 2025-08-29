This directory hosts Bootstrap theme assets for the project.

How to use:
- Place your custom Bootstrap CSS here (e.g., theme.css or a Bootswatch .min.css file).
- Optionally place JS overrides and images under the same folder.
- Reference the theme CSS in templates (e.g., enemygen/templates/base.html) after the Bootstrap CDN link and before base.css, for example:

  {% load static %}
  <link rel="stylesheet" href="{% static 'themes/bootstrap/theme.css' %}?v=1" />

Notes:
- Keep theme-specific assets inside static/themes/bootstrap to keep the static tree organized.
- If you add multiple themes, create additional subfolders under static/themes/ (e.g., themes/darkly, themes/flatly).
