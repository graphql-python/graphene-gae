.. :changelog:

History
-------
1.0.7 (TBD)
-----------
* GraphQLHandler GET supoort ([PR #27](https://github.com/graphql-python/graphene-gae/pull/27))

1.0.6 (2016-12-06)
------------------
* Fixed DeadlineExceededError import swo connections properly handle timeouts

1.0.5 (2016-11-23)
------------------
* Improved behavior of `NdbConnectionField` when `transform_edges` also filters out some edges ([PR #26](https://github.com/graphql-python/graphene-gae/pull/25))

1.0.3 (2016-11-22)
------------------
* Added `transform_edges` to `NdbConnectionField` ([PR #25](https://github.com/graphql-python/graphene-gae/pull/25))

1.0.2 (2016-10-20)
------------------
* Added `_handle_graphql_errors` hook to GraphQLHandler

1.0.1 (2016-09-28)
------------------
* Added missing support for StructuredProperty

1.0 (2016-09-26)
----------------
* Upgraded to Graphene 1.0

0.1.9 (2016-08-17)
---------------------
* Each NdbObject now exposes an `ndbId` String field that maps to the entity's `key.id()`
* Added ndb boolean argument to NdbKeyStringField so now when looking at KeyProperty we can fetch either global GraphQL id or the NDB internal id.


0.1.8 (2016-08-16)
---------------------
* Made connection_from_ndb_query resilient to random ndb timeouts


0.1.7 (2016-06-14)
---------------------
* BREAKING: Fixed behavior of KeyProperty to expose GraphQL Global IDs instead of internal ndb.Key values. ([PR #16](https://github.com/graphql-python/graphene-gae/pull/16))

0.1.6 (2016-06-10)
---------------------
* Changing development status to Beta
* Added NdbNode.global_id_to_key [PR #15](https://github.com/graphql-python/graphene-gae/pull/15)

0.1.5 (2016-06-08)
---------------------
* Fixed behavior of ndb.KeyProperty ([PR #14](https://github.com/graphql-python/graphene-gae/pull/14))

0.1.4 (2016-06-02)
---------------------
* NdbConnectionField added arguments that can be used in quert:
    * keys_only - to execute a keys only query
    * batch_size - to control the NDB query iteration batch size
    * page_size - control the page sizes when paginating connection results
* Added support for LocalStructuredProperty.
    * Given a property `ndb.LocalStructuredType(Something)` it will automatically
      map to a Field(SomethingType) - SomethingType has to be part of the schema.
    * Support for `repeated` and `required` propeties.


0.1.3 (2016-05-27)
---------------------
* Added `graphene_gae.webapp2.GraphQLHandler` - a basic HTTP Handler to process GraphQL requests


0.1.1 (2016-05-25)
---------------------

* Updated graphene dependency to latest 0.10.1 version.
    * NdbConnection.from_list now gets context as parameter


0.1.0 (2016-05-11)
---------------------

* First release on PyPI.
