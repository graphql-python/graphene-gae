from tests.base_test import BaseTest

from google.appengine.ext import ndb

from graphql_relay import to_global_id

from examples.starwars.models import Ship
from examples.starwars.data import initialize
from examples.starwars.schema import schema

__author__ = 'ekampf'


class TestStarWarsMutation(BaseTest):
    def setUp(self):
        super(TestStarWarsMutation, self).setUp()
        initialize()

    def testIntroduceShip(self):
        query = '''
            mutation MyMutation {
              introduceShip(input:{clientMutationId:"abc", shipName: "XYZWing", factionId: "rebels"}) {
                ship {
                  id
                  name
                }
                faction {
                  name
                  ships {
                    edges {
                      node {
                        id
                        name
                      }
                    }
                  }
                }
              }
            }
            '''

        expected = {
            'introduceShip': {
                'ship': {
                    'id': 'U2hpcDoxMQ==',
                    'name': 'XYZWing'
                },
                'faction': {
                    'name': 'Alliance to Restore the Republic',
                    'ships': {
                        'edges': [{
                            'node': {
                                'id': 'U2hpcDphaEZuY21Gd2FHVnVaUzFuWVdVdGRHVnpkSElLQ3hJRVUyaHBjQmdEREE=',
                                'name': 'X-Wing'
                            }
                        }, {
                            'node': {
                                'id': 'U2hpcDphaEZuY21Gd2FHVnVaUzFuWVdVdGRHVnpkSElLQ3hJRVUyaHBjQmdFREE=',
                                'name': 'Y-Wing'
                            }
                        }, {
                            'node': {
                                'id': 'U2hpcDphaEZuY21Gd2FHVnVaUzFuWVdVdGRHVnpkSElLQ3hJRVUyaHBjQmdGREE=',
                                'name': 'A-Wing'
                            }
                        }, {
                            'node': {
                                'id': 'U2hpcDphaEZuY21Gd2FHVnVaUzFuWVdVdGRHVnpkSElLQ3hJRVUyaHBjQmdHREE=',
                                'name': 'Millenium Falcon'
                            }
                        }, {
                            'node': {
                                'id': 'U2hpcDphaEZuY21Gd2FHVnVaUzFuWVdVdGRHVnpkSElLQ3hJRVUyaHBjQmdIREE=',
                                'name': 'Home One'
                            }
                        }, {
                            'node': {
                                'id': 'U2hpcDphaEZuY21Gd2FHVnVaUzFuWVdVdGRHVnpkSElLQ3hJRVUyaHBjQmdMREE=',
                                'name': 'XYZWing'
                            }
                        }]
                    },
                }
            }
        }
        result = schema.execute(query)
        ship_in_db = Ship.query().filter(Ship.name == 'XYZWing', Ship.faction_key == ndb.Key('Faction', 'rebels')).fetch(1)

        self.assertIsNotNone(ship_in_db)
        self.assertLength(ship_in_db, 1)

        new_ship = ship_in_db[0]
        self.assertEqual(new_ship.name, 'XYZWing')

        expected['introduceShip']['ship']['id'] = to_global_id('Ship', new_ship.key.urlsafe())

        self.assertFalse(result.errors, msg=str(result.errors))
        self.assertDictEqual(result.data, expected)
