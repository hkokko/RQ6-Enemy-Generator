### **Pull Request Description: Enforce Access Restrictions and Privacy**

#### **Summary**
This Pull Request implements strict access controls for enemy templates and parties, ensuring that unpublished content is only accessible to its owner. It also refines the JSON API to respect user privacy while still allowing owners to access their own unpublished work.

#### **Motivation**
Previously, unpublished templates and parties could be accessed by any user if the direct URL was known. This update ensures privacy for users' work-in-progress creations, aligning the application with expected security and privacy standards.

#### **Changes**
- **Access Control Enforcement**: Modified `enemy_template` and `party` views to check for ownership before displaying unpublished content. Unauthorized access now correctly results in a `Http404`.
- **Privacy-Aware JSON API**: Updated the `index_json` and `party_index_json` endpoints to filter out unpublished templates belonging to other users. Added names to these URL patterns for easier referencing.
- **Improved Data Filtering**: Refined `get_enemy_templates` and `get_party_templates` utility functions to handle ownership-based filtering. Logged-in users can now see their own unpublished content in both the web UI and JSON API.
- **Modernized Test Suite**: Replaced numerous instances of deprecated `assertEquals` with `assertEqual` to ensure compatibility with modern Django/Python testing frameworks.
- **Enhanced Test Coverage**: Added a new test class `TestViewFiltering` that comprehensively covers privacy scenarios for both enemy templates and parties, including owner access, unauthorized access, and anonymous access.

#### **Verification**
- Verified that `Http404` is raised when accessing someone else's unpublished template or party.
- Verified that owners can still access and view their own unpublished templates/parties in both the detail views and the JSON API.
- Confirmed that the JSON API correctly excludes unpublished items from other users.
- Ran the full test suite (`python manage.py test`) and confirmed that all tests pass.
