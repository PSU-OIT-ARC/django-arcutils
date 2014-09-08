from django.db.models.sql.compiler import SQLCompiler

# This monkey patch allows us to write subqueries in the `tables` argument to the
# QuerySet.extra method. For example Foo.objects.all().extra(tables=["(SELECT * FROM Bar) t"])
# See: http://djangosnippets.org/snippets/236/#c3754
_quote_name_unless_alias = SQLCompiler.quote_name_unless_alias
SQLCompiler.quote_name_unless_alias = lambda self, name: name if name.strip().startswith('(') else _quote_name_unless_alias(self, name)
