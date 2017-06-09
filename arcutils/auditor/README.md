# Auditor App

The Auditor app is used to keep track of changes to model records.

## Setup

- Add `arcutils.auditor` to `INSTALLED_APPS`; make sure this is after
  all the apps that contain models being audited.
- Add `arcutils.threadlocals.ThreadLocalMiddleware` to `MIDDLEWARE`.
- Add `arcutils.auditor.middleware.AuditorMiddleware` to `MIDDLEWARE`.
- Configure the models and fields to audit:

    AUDITOR = {
        'models': [{
            'name': 'articles.Article',
            'fields': ['body', 'status']
        }]
- Run migrations for the `auditor` app.

Now, changes to the specified fields of the specified models will be
logged. Creation and deletion are logged as well.

All changes made to any audited models/fields in a given request will
have the same user and timestamp and will be grouped together with
a changeset ID. Within a changeset, log records are sequenced according
to the order changes were made. Old and new values are saved as JSON.

## Viewing the Log

Currently, there are no default views for log records. There's an
example in the `ohslib.articles` app.
