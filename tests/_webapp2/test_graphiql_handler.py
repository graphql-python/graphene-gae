from tests.base_test import BaseTest

import webtest
from graphene_gae.webapp2 import graphql_application

__author__ = 'ekampf'


class TestGraphiQLHandler(BaseTest):
    def setUp(self):
        BaseTest.setUp(self)

        self.app = webtest.TestApp(graphql_application)

    def testGET(self):
        response = self.app.get('/graphiql')
        self.assertEqual(response.status_code, 200)
