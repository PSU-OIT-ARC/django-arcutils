# Change Log for ARCUtils

## 2.19.0 - 2017-06-19

### Major Changes

- Added `auditor` app. This is used to log changes to specified model
  fields. Should be considered a work in progress for now.

### Minor Changes

- Added custom 400 and 500 error views. These pass the request context
  to the template renderer so that templates can be rendered correctly.
- Removed global `ARCUTILS_PACKAGE_DIR` from `settings`. The ARCUtils
  package directory is now retrieved only when `init_settings()` is
  called.
- Added additional default settings in `init_settings()`:
  - `UP_TIME`: an object with a `current` property that returns the
    current uptime (by subtracting the current time from the existing
    `START_TIME` setting)
  - `VERSION`: the project version retrieved via `pkg_resources`

### Other Changes

- Upgraded djangorestframework 3.6.2 => 3.6.3
- Upgraded ldap3 2.2.2 => 2.2.4
- Upgraded raven 6.0.0 => 6.1.0
- Fixed double-printing of `end` in color printer
- Replaced deprecated `log.warn()` with `log.warning()`


## 2.18.0 - 2017-05-03

- Made the masquerade app more RESTful. In particular, it's now possible
  to request a JSON response from its select (user) view. Because of
  this, the user data it returns is now serialized using a DRF model
  serializer; I don't think this will cause any backward-compatibility
  issues, but it might.


## 2.17.0 - 2017-04-27

- Added support for Python 3.6.
- Started adding support for Django 1.11.
- Upgraded DRF 3.5 => 3.6.
- Removed default `STATICFILES_DIRS` local setting. This isn't needed in
  the case where `arcutils` and the project are in `INSTALLED_APPS`--
  which is the common case--since static directories in apps are
  included by default.
- Added custom `collectstatic` Django management command with
  `--exclude` and `--include` options. Unlike the built in `--ignore`
  option, these match against whole paths instead of path segments. In
  addition, if a file is `--include`d it will be included even if it was
  previously ignored or excluded; this is useful when ignoring a big
  directory like `node_modules` that contains a file or two that should
  be included (e.g., `almond.js`).
- Updated tasks/commands for latest version of ARCTasks.


## 2.16.0 - 2017-02-13

### Major Changes

- Reimplemented `settings.get_setting()` and `PrefixedSettings` so they
  use django-local-settings' dotted item functionality internally. This
  makes these simpler and more consistent with other settings access in
  ARC/WDT projects. The major external difference is that a `KeyError`
  will be raised now instead of a `SettingNotFoundError`. In addition,
  it's now possible to traverse into settings values.
- Enhanced group handling in `UserMixin`. Groups can now be `Group`
  objects in addition to group names. This was copied over from ohslib
  so that ohslib could use ARCUtils' `UserMixin`.
- When Django 1.10 is in use, the `MIDDLEWARE_CLASSES` setting is now
  automatically removed from settings (assuming the `MIDDLEWARE` setting
  is present and set).
- Added `settings_processors` option to `settings.init_settings()`. This
  makes it easy to modify settings if needed.

### Other Changes

- Upgraded django-local-settings 1.0b3 => 1.0b5.
- Upgraded tox 2.5.0 => 2.6.0.
- Improved tox.ini; in particular, test each version of Python in order,
  and each version of Django in order for each version of Python.
- Started adding support for Python 3.6 and Django 1.11 (the latter is
  still in alpha).
- Added `<package>.staging.rc.pdx.edu` to default stage `ALLOWED_HOSTS`.
- Added `show_upgraded_packages` task from ARCTasks.
- `settings.init_settings()` now returns the `settings` dict its passed.
  This seems like it could potentially be useful, whereas returning
  `None` isn't.


## 2.15.0 - 2017-01-27

- Added `findunusedtemplates` Django management command (works pretty
  well but could be improved).
- Added `showsettings` Django management command.
- Set default database for dev and test to `localhost`. This is intended
  to be more reliable than depending on a local socket connection. It's
  also more compatible with some Docker setups.
- Improved `wsgi.py` by allowing the root and virtualenv directories to
  be specified via the `WSGI_ROOT` and `WSGI_VENV` environment
  variables.  This is another change supporting Docker setups.
- Added `redirect_location` template tag, which is a wrapper for
  `response.get_redirect_location()`. The former is much easier to use
  in templates versus adding a var to the template context in the view.


## 2.14.0 - 2016-12-12

- Added basic Sentry support. Added raven (Python Sentry client) to
  dependencies and added `raven.contrib.django.raven_compat` to
  `INSTALLED_APPS`. This makes the assumption that we (eventually) want
  to use Sentry in all (or at least most) projects.
- Updated default dev and test settings to use package name as database
  username instead of defaulting to the current OS user. This goes with
  a corresponding change in ARCTasks that creates a database user named
  after the package when creating databases.
- Upgraded ldap3 1.x to 2.x (1.4.0 => 2.1.1). This required a few
  tweaks, but the ARCUtils LDAP API is essentially unchanged.
- Upgraded DRF 3.4.x => 3.5.x. This is used only in dev and testing.
- Added default DRF renderer settings for all environments. These
  defaults are based on the notion that most projects will have an
  (Angular?) front end talking to a RESTful back end. Proposed by
  @conwayb.
- Improved `require_block` template tag. Made it more flexible with
  regard to the path prefix for `require.js` or `almond.js`. The
  `ARC.require_block.prefix` setting can be used to override the default
  `vendor` prefix.


## 2.13.0 - 2016-10-07

- Made all middleware compatible with Django 1.10 and above. Did so by
  reimplementing all middleware for Django 1.10 and then adding shims
  for Django 1.9 and below.
- Added `drop` arg to `init_settings()`; this allows projects to drop
  unused, cluttering settings.


## 2.12.0 - 2016-10-03

- Added official support for Python 3.5.
- Dropped official support for Django 1.7.
- Started adding support for Django 1.10.
- Improved default WSGI script.
- Started using tox to test multiple Python/Django combinations.
- Fixed up some settings-related stuff (low level internal stuff that
  likely has no observable effect).
- Added default `AUTH_PASSWORD_VALIDATORS` because we shouldn't allow
  users to have terrible passwords.
- Fixed Bootstrap stylesheet link in foundation.html.
- Upgraded DRF 3.4 => 3.4.7, which required some internal changes to
  our `TemplateHTMLContextDictRenderer`.
- pytz is now included as a default dependency.
- Upgraded ldap3 1.2.2 => 1.4.0.


## 2.11.1 - 2016-07-01

Revert back to using StaticFilesStorage by default in staging.


## 2.11.0 - 2016-06-30

### Added

- Added `PrefixedSettings`. This provides a nice way to specify defaults
  for a group of settings (e.g., for a Django app or package) and to get
  access to a group of settings.
  NOTE: There's more detail about this in the `Changed` section below.
- Added `SECURE_PROXY_SSL_HEADER` to default stage local settings.
  This is needed (only) in staging because the main Apache instance
  proxies to app-specific Apache instances.

### Changed

- Constrained Django version depending on Python version: 1.8 is
  installed on Python<=3.3; 1.9 is installed on Python>=3.4.
- Disabled all logging in default test local settings by using a
  `NullHandler`.
- `clearsessions` is now run nightly by default (when the `wsgi.py`
  template provided by ARCUtils is used).
- Replaced `make_prefixed_get_setting` function with `PrefixedSettings`
  class; the latter provides the same functionality, but is perhaps
  easier to understand, and its usage is more similar to regular Django
  settings (it provides dict-like access to the prefixed settings).
  NOTE: This is a breaking change, but `make_prefixed_get_setting` has
  so far only been used internally in ARCUtils. `PrefixedSettings` is
  more suitable for use externally.
- Removed unused `_suffix` arg from `CASBackend._validate_ticket`.

### Fixed

- Corrected import path to `NestedObjects`; Django standardized all
  utility module names in 1.7 (`util` => `utils`).
- Made Django's `ManifestStaticFilesStorage` the default in stage local
  settings. Not sure what the rationale was for this being different
  from production before.


## 2.10.0 - 2016-05-05

- Corrected default ARC.cdn.paths.jquery-js setting.
- Added ARC-specific Django Admin stuff (added top level `admin`
  module).


## 2.9.1 - 2016-04-11

## Fixed

Fixed creation of users when using CAS auth. Previously, the `username`
attribute wasn't being set; now it is. This regression was introduced
when the use of CAS callbacks was deprecated in 2.8.0.


## 2.9.0 - 2016-04-07

Upgraded django-local-settings from 1.0a17 to 1.0a20. 1.0a20 is
*backward incompatible* with 1.0a19 in that it uses `{...}` for
interpolation groups instead of `{{...}}`. In addition, since
`str.format()` is no longer used to do interpolation, `{{X[y]}}` won't
work now; you have to use `{{X.y}}` instead (which is actually a *good*
thing).

This change also means that this version of ARCUtils is backward
incompatible, but it's not *majorly* incompatible, so I don't think
bumping the major version is appropriate in this case.


## 2.8.2 - 2016-03-31

- Improved help text shown for default `SECRET_KEY` local setting; since
  it's a secret settings, we can't set a default, so we want to indicate
  that the value shown is a suggestion. It's also quoted now for easier
  copypasta.
- Added default `GOOGLE.analytics.tracking_id setting = null` stage
  setting since Google Analytics isn't typically used in staging, and
  being prompted for it is annoying.


## 2.8.1 - 2016-03-29

Fix the default `ARC.cdn.paths` local setting and improve its docs and
examples also.

## 2.8.0 - 2016-03-28

*Note: This version has a bug relating to the creation of users when CAS
authentication is used, which was fixed in 2.9.1.*

### Added

- Default `MEDIA_ROOT` and `STATIC_ROOT` test settings. If these aren't
  set, media and static files created during testing might end up in the
  current directory, which is annoying.

### Deprecated

- The use of CAS response callbacks is now deprecated. A `CASBackend` or
  `CASModelBackend` subclass with an overridden `create_user` method
  should be used instead. It was too confusing having multiple ways of
  creating users from CAS data. `create_user` also makes it convenient
  to override or set additional user attributes from subclasses.

### Fixed

- Fixed how `START_TIME` setting is set in `init_settings` to keep an
  `ImproperlyConfigured` exception from being raised.

### Upgraded

- ldap3 1.1.2 => 1.2.2

## 2.7.0 - 2016-03-21

- Added ARCTasks as a dev dependency for its release tasks.
- Upgraded django-local-settings 1.0a14 => 1.0a17. Note that for now
  this means settings values can't contain embedded curly braces that
  are *not* intended for interpolation.

## 2.6.0 - 2016-03-21

### Added

- Added `ROOT_DIR` setting for use in dev only (when `init_settings()`
  is used).
- Added `START_TIME` setting (when `init_settings()` is used).
- Added more default local settings (when `init_local_settings() is
  used).

### Changed

- Switched to new name for PostgreSQL database back end (`postgresql`).
  Projects still using Django 1.7 or earlier will need to override this
  to use the old name (`postgresql_psycopg2`).
- Bumped default Bootstrap version from 3.3.5 => 3.3.6.

### Fixed

- Fixed how `PACKAGE` setting is initialized when using
  `init_settings()`.

## 2.5.0 - 2016-03-16

- Added DRF router with "proper" trailing slash policy: list/collection
  routes end with a slash; detail/member routes don't. This is nicer and
  also easier to use with AngularJS $resource routes.

## 2.4.0 - 2016-03-16

- Upgraded ldap3 from 1.0.4 to 1.1.2
- Made copying of wsgi.py more convenient.

## 2.3.0 - 2016-03-04

- Made `settings` arg to `init_settings()` public
- Renamed `settings.get_settings()` to `settings.get_module_globals()`
  for clarity
- Improved & standardized default settings for `cas`, `ldap`, and
  `masquerade` packages
- Upgraded certifi 2015.11.20.1 => 2016.2.28
- Upgraded django-local-settings 1.0a13 => 1.0a14

## 2.2.1 - 2016-02-10

### Fixed

- CAS: Add `CASBackend.get_user()` method (a copy of
  `ModelBackend.get_user()`); this is necessary for `CASBackend` to
  actually be used as an auth backend.

## 2.2.0 - 2016-02-09

### Added

- Testing: Added `patch_json` method to our test `Client`.

### Changed

- LDAP: Reverted to SYNC as default connection strategy. We're really
  thrashing around on this, and I can't tell if it's because of how the
  LDAP service is setup, bugs in the ldap3 library, or bugs in our code.
  One thing to recommend the SYNC strategy is that its code is actually
  readable in the ldap3 code base. The other strategies are a mess.
- LDAP: Changed default value for `auto_bind` connection option to
  `AUTO_BIND_NONE` to match the ldap3 default (instead of using `True`,
  which is equivalent to `AUTO_BIND_NO_TLS`).
- LDAP: Split the `ldap` module up into various modules in a new `ldap`
  package; the module was getting unwieldy, and this paves the way
  toward some parsing-related refactoring I plan on doing at some point.

### Fixed

- LDAP: Wait for search responses inside `with connection` block;
  the connection can become unbound while waiting outside the `with`
  block, which can cause errors in some cases (esp. w/ TLS it seems).

## 2.1.0 - 2016-02-04

### Added

- LDAP: The `arcutils ldap` console script gained two new options:
  `--search-base` and `--attibutes`; these correspond `ldapsearch()`
  keyword args
- LDAP: More tests, especially of phone number parsing

### Changed

- LDAP: Set the default value of the `attributes` keyword arg of
  `ldapsearch()` to `None`; this way, `None` can be passed to
  indicate that the default set of attributes should be fetched
- LDAP: Allow default attributes fetched for connections to be
  specified via `LDAP.{name}.attributes` settings
- LDAP: Change order of `attributes` and `parse` keyword args to
  `ldapsearch()`
- LDAP: Make phone number parsing more robust

### Fixed

- LDAP: Only include extension in user profile if the user's phone
  number looks like a PSU number
- LDAP: Don't include `None` in the list of email addresses
- LDAP: Don't return 'None@pdx.edu' as a fallback email address (i.e.,
  when the LDAP attributes don't contain a username field)

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
