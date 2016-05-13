from tests.base_test import BaseTest

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
                'id': 'RmFjdGlvbjpyZWJlbHM=',
                'name': 'Alliance to Restore the Republic'
            }
        }
        result = schema.execute(query)
        self.assertFalse(result.errors, msg=str(result.errors))
        self.assertDictEqual(result.data, expected)

    def test_correctly_refetches_rebels(self):
        query = '''
            query RebelsRefetchQuery {
              node(id: "RmFjdGlvbjpyZWJlbHM=") {
                id
                ... on Faction {
                  name
                }
              }
            }
          '''
        expected = {
            'node': {
                'id': 'RmFjdGlvbjpyZWJlbHM=',
                'name': 'Alliance to Restore the Republic'
            }
        }
        result = schema.execute(query)
        self.assertFalse(result.errors, msg=str(result.errors))
        self.assertDictEqual(result.data, expected)

    def test_correctly_fetches_id_name_empire(self):
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
                'id': 'RmFjdGlvbjplbXBpcmU=',
                'name': 'Galactic Empire'
            }
        }
        result = schema.execute(query)
        self.assertFalse(result.errors, msg=str(result.errors))
        self.assertDictEqual(result.data, expected)

    def test_correctly_refetches_id_name_empire(self):
        query = '''
            query EmpireRefetchQuery {
              node(id: "RmFjdGlvbjplbXBpcmU=") {
                id
                ... on Faction {
                  name
                }
              }
            }
          '''
        expected = {
            'node': {
                'id': 'RmFjdGlvbjplbXBpcmU=',
                'name': 'Galactic Empire'
            }
        }
        result = schema.execute(query)
        self.assertFalse(result.errors, msg=str(result.errors))
        self.assertDictEqual(result.data, expected)
