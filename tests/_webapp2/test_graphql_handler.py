from tests.base_test import BaseTest

import webapp2
import graphene

from graphene_gae.webapp2 import graphql_application

__author__ = 'ekampf'


schema = graphene.Schema()


graphql_application.config['graphql_schema'] = schema
graphql_application.config['graphql_pretty'] = True


class TestGraphQLHandler(BaseTest):
    def testPOST_noInput_returns400(self):
        request = webapp2.Request.blank('/graphql')
        request.method = 'POST'
        response = request.get_response(graphql_application)

        self.assertEqual(response.status_int, 400)

