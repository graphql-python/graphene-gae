from tests.base_test import BaseTest

from examples.starwars.data import initialize
from examples.starwars.schema import schema

__author__ = 'ekampf'


class TestStarWarsConnections(BaseTest):
    def setUp(self):
        super(TestStarWarsConnections, self).setUp()
        initialize()

    def testConnection(self):
        query = '''
            query RebelsShipsQuery {
              rebels {
                name,
                hero {
                  name
                }
                ships(first: 1) {
                  edges {
                    node {
                      name
                    }
                  }
                }
              }
            }
            '''
        expected = {
            'rebels': {
                'name': 'Alliance to Restore the Republic',
                'hero': {
                    'name': 'Human'
                },
                'ships': {
                    'edges': [
                        {
                            'node': {
                                'name': 'X-Wing'
                            }
                        }
                    ]
                }
            }
        }
        result = schema.execute(query)
        self.assertFalse(result.errors, msg=str(result.errors))
        self.assertDictEqual(result.data, expected)
