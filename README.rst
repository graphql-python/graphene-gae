===============================
Graphene GAE
===============================

.. image:: https://travis-ci.org/graphql-python/graphene-gae.svg?branch=master
        :target: https://travis-ci.org/graphql-python/graphene-gae

.. image:: https://coveralls.io/repos/github/graphql-python/graphene-gae/badge.svg?branch=master
        :target: https://coveralls.io/github/graphql-python/graphene-gae?branch=master

.. image:: https://img.shields.io/pypi/v/graphene-gae.svg
        :target: https://pypi.python.org/pypi/graphene-gae



A Google AppEngine integration library for `Graphene <http://graphene-python.org>`__

* Free software: BSD license
* Documentation: https://graphene_gae.readthedocs.org.

Upgrade Notes
-------------
If you're upgrading from an older version (pre 2.0 version) 
please check out the `Graphene Upgrade Guide <https://github.com/graphql-python/graphene/blob/master/UPGRADE-v2.0.md>`__.


Installation
------------

To install Graphene-GAE on your AppEngine project, go to your
project folder and runthis command in your shell:

.. code:: bash

    pip install graphene-gae -t ./libs

This will install the library and its dependencies to the `libs` folder
under your projects root - so the dependencies get uploaded withyour GAE
project when you publish your app.

Make sure the `libs` folder is in your python path by adding the following
to your `appengine_config.py`:

.. code:: python

    import sys

    for path in ['libs']:
        if path not in sys.path:
            sys.path[0:0] = [path]


Examples
--------

Here's a simple GAE model:

.. code:: python

    class Article(ndb.Model):
        headline = ndb.StringProperty()
        summary = ndb.TextProperty()
        text = ndb.TextProperty()

        author_key = ndb.KeyProperty(kind='Author')

        created_at = ndb.DateTimeProperty(auto_now_add=True)
        updated_at = ndb.DateTimeProperty(auto_now=True)

To create a GraphQL schema for it you simply have to write the following:

.. code:: python

    import graphene
    from graphene_gae import NdbObjectType

    class ArticleType(NdbObjectType):
        class Meta:
            model = Article

    class Query(graphene.ObjectType):
        articles = graphene.List(ArticleType)

        @graphene.resolve_only_args
        def resolve_articles(self):
            return Article.query()

    schema = graphene.Schema(query=QueryRoot)

Then you can simply query the schema:

.. code::python

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

To learn more check out the following `examples <examples/>`__:

* `Starwars <examples/starwars>`__

Contributing
------------

After cloning this repo, ensure dependencies are installed by running:

.. code:: sh

    make deps
    make install

Make sure tests and lint are running:

.. code:: sh

    make test
    make lint
