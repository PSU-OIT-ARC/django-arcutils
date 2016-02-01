œ# Change Log

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## 2.0.0 - 2016-02-01

Version 2 revamps ARCUtils to be more of a library.

Below is a summary of the differences between v1 and v2. This summary
should not be considered exhaustive.

### Notable differences from v1:

- No longer supports Python 2; supports only Python 3.3+
- No longer configures any functionality via Django `AppConfig`
- No longer adds template tags to Django's built-ins
- No longer does any monkey-patching
- Improves & expands on existing LDAP functionality
- Consolidates generally-useful stuff implemented in various ARC apps;
  e.g., base model and test classes
- Adds a separate `tests` package & more tests
- Lots of cleanup

### Notable removals:

- `logging` module; logging config is now handled exclusively via
  settings
- Inlined django-bootstrap-form package
- Some old template tags (although some were kept but deprecated to make
  migrating from v1 to v2 easier)
- Empty `admins` and `views` modules; newer versions of Django no longer
  require these
- All usage of the `model_mommy` package
- Automatic session-clearing functionality; this can now be easily set
  up to run as a daily task (see below)

### Notable additions:

- Direct support for local settings
- A default set of local settings that should be suitable for most ARC
  apps (or at least a good starting point)
- Basic base.html template for getting up-and-running
- Various template tags such as `google_analytics`, `jsonify`, and
  `markdown`
- Masquerade app; similar to django-cloak, but simpler
- arcutils console script
  - ldap subcommand
- PSU-specific CAS functionality
  - Third party libs seem unmaintained and didn't provide some config
    options we need
  - Simpler than third party libs since it only implements the minimal
    functionality we need
- Simple daily tasks runner
  - Removes the need to use cron or Celery for simple once-a-day tasks
    like rebuilding search indexes
  - Removes the need for installing, e.g., session cleanup as a
    request_finished handler

## 1.1.1 - 2015-06-23

### Fixed

- The monkey patch for the PasswordResetForm blindly overwrote the
  clean_email method. This would break subclasses (or other monkey patches)
  that implemented a clean_email method. It now plays nicely with others.

## 1.1.0 - 2015-03-12

Made a few changes to support Django 1.8.

## 1.0.0 - 2015-03-12

Initial version.
