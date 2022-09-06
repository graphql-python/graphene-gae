# Graphene GAE (deprecated!)

> :warning: This repository is deprecated due to lack of maintainers.
If you're interested in taking over let us know via [the Graphene
Slack](https://join.slack.com/t/graphenetools/shared_invite/enQtOTE2MDQ1NTg4MDM1LTA4Nzk0MGU0NGEwNzUxZGNjNDQ4ZjAwNDJjMjY0OGE1ZDgxZTg4YjM2ZTc4MjE2ZTAzZjE2ZThhZTQzZTkyMmM)

A Google AppEngine integration library for
[Graphene](http://graphene-python.org)

-   Free software: BSD license
-   Documentation: <https://graphene_gae.readthedocs.org>.

## Upgrade Notes

If you're upgrading from an older version (pre 2.0 version) please check
out the [Graphene Upgrade
Guide](https://github.com/graphql-python/graphene/blob/master/UPGRADE-v2.0.md).

## Installation

To install Graphene-GAE on your AppEngine project, go to your project
folder and runthis command in your shell:

``` bash
pip install graphene-gae -t ./libs
```

This will install the library and its dependencies to the <span
class="title-ref">libs</span> folder under your projects root - so the
dependencies get uploaded withyour GAE project when you publish your
app.

Make sure the <span class="title-ref">libs</span> folder is in your
python path by adding the following to your \`appengine_config.py\`:

``` python
import sys

for path in ['libs']:
    if path not in sys.path:
        sys.path[0:0] = [path]
```

## Examples

Here's a simple GAE model:

``` python
class Article(ndb.Model):
    headline = ndb.StringProperty()
    summary = ndb.TextProperty()
    text = ndb.TextProperty()

    author_key = ndb.KeyProperty(kind='Author')

    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)
```

To create a GraphQL schema for it you simply have to write the
following:

``` python
import graphene
from graphene_gae import NdbObjectType

class ArticleType(NdbObjectType):
    class Meta:
        model = Article

class QueryRoot(graphene.ObjectType):
    articles = graphene.List(ArticleType)

    @graphene.resolve_only_args
    def resolve_articles(self):
        return Article.query()

schema = graphene.Schema(query=QueryRoot)
```

Then you can simply query the schema:

``` python
query = '''
    query GetArticles {
      articles {
        headline,
        summary,
        created_at
      }
    }
'''
result = schema.execute(query)
```

To learn more check out the following [examples](examples/):

-   [Starwars](examples/starwars)

## Contributing

After cloning this repo, ensure dependencies are installed by running:

``` sh
make deps
make install
```

Make sure tests and lint are running:

``` sh
make test
make lint
```
