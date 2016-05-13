from tests.base_test import BaseTest

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
                                'id': 'U2hpcDoz',
                                'name': 'X-Wing'
                            }
                        }, {
                            'node': {
                                'id': 'U2hpcDo0',
                                'name': 'Y-Wing'
                            }
                        }, {
                            'node': {
                                'id': 'U2hpcDo1',
                                'name': 'A-Wing'
                            }
                        }, {
                            'node': {
                                'id': 'U2hpcDo2',
                                'name': 'Millenium Falcon'
                            }
                        }, {
                            'node': {
                                'id': 'U2hpcDo3',
                                'name': 'Home One'
                            }
                        }, {
                            'node': {
                                'id': 'U2hpcDoxMQ==',
                                'name': 'XYZWing'
                            }
                        }]
                    },
                }
            }
        }
        result = schema.execute(query)
        self.assertFalse(result.errors, msg=str(result.errors))
        self.assertDictEqual(result.data, expected)
