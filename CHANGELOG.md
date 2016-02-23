# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [1.2.0] - 2016-02-23

### Added

- `cas` package backported from ARCUtils v2 (our own implementation of
  a CAS back end that supports Shibboleth CAS)
- `response` module (for `get_redirect_location()`, which is used in the
  `cas` package.

### Changed/Fixed

- General package maintenance and cleanup.

## [1.1.1] - 2015-06-23

# Fixed
- The monkey patch for the PasswordResetForm blindly overwrote the
  clean_email method. This would break subclasses (or other monkey patches)
  that implemented a clean_email method. It now plays nicely with others.

## [1.1.0] - 2015-03-12

Made a few changes to support Django 1.8.

## [1.0.0] - 2015-03-12

### Added
- Everything
