from tests.base_test import BaseTest

from google.appengine.ext import ndb

from graphql_relay import to_global_id

from examples.starwars.data import initialize
from examples.starwars.schema import schema

__author__ = 'ekampf'


class TestStarWarsObjectIdentification(BaseTest):
    def setUp(self):
        super(TestStarWarsObjectIdentification, self).setUp()
        initialize()

    def test_correctly_fetches_id_name_rebels(self):
        query = '''
            query RebelsQuery {
              rebels {
                id,
                name
              }
            }
          '''
        expected = {
            'rebels': {
                'id': to_global_id('Faction', ndb.Key('Faction', 'rebels').urlsafe()),
                'name': 'Alliance to Restore the Republic'
            }
        }
        result = schema.execute(query)
        self.assertFalse(result.errors, msg=str(result.errors))
        self.assertDictEqual(result.data, expected)

    def test_correctly_refetches_rebels(self):
        rebels_key = to_global_id('Faction', ndb.Key('Faction', 'rebels').urlsafe())
        query = '''
            query RebelsRefetchQuery {
              node(id: "%s") {
                id
                ... on Faction {
                  name
                }
              }
            }
          ''' % rebels_key

        expected = {
            'node': {
                'id': rebels_key,
                'name': 'Alliance to Restore the Republic'
            }
        }
        result = schema.execute(query)
        self.assertFalse(result.errors, msg=str(result.errors))
        self.assertDictEqual(result.data, expected)

    def test_correctly_fetches_id_name_empire(self):
        empire_key = to_global_id('Faction', ndb.Key('Faction', 'empire').urlsafe())
        query = '''
          query EmpireQuery {
            empire {
              id
              name
            }
          }
        '''
        expected = {
            'empire': {
                'id': empire_key,
                'name': 'Galactic Empire'
            }
        }
        result = schema.execute(query)
        self.assertFalse(result.errors, msg=str(result.errors))
        self.assertDictEqual(result.data, expected)

    def test_correctly_refetches_id_name_empire(self):
        empire_key = to_global_id('Faction', ndb.Key('Faction', 'empire').urlsafe())
        query = '''
            query EmpireRefetchQuery {
              node(id: "%s") {
                id
                ... on Faction {
                  name
                }
              }
            }
          ''' % empire_key
        expected = {
            'node': {
                'id': empire_key,
                'name': 'Galactic Empire'
            }
        }
        result = schema.execute(query)
        self.assertFalse(result.errors, msg=str(result.errors))
        self.assertDictEqual(result.data, expected)
