import webapp2
from tests.base_test import BaseTest

import json
import webtest
import graphene
from graphene import relay
from graphene_gae.webapp2 import graphql_application, GraphQLHandler

__author__ = 'ekampf'


class QueryRootType(graphene.ObjectType):
    default_greet = 'World'

    greet = graphene.Field(graphene.String, who=graphene.Argument(graphene.String))
    resolver_raises = graphene.String()

    @graphene.resolve_only_args
    def resolve_greet(self, who):
        return 'Hello %s!' % who

    def resolve_resolver_raises(self, *_):
        raise Exception("TEST")


class ChangeDefaultGreetingMutation(relay.ClientIDMutation):
    class Input:
        value = graphene.String()

    ok = graphene.Boolean()
    defaultGreeting = graphene.String()

    @classmethod
    def mutate_and_get_payload(cls, input, context, info):
        QueryRootType.default_greet = input.get('value')
        return ChangeDefaultGreetingMutation(ok=True, defaultGreeting=QueryRootType.default_greet)


class MutationRootType(graphene.ObjectType):
    changeDefaultGreeting = ChangeDefaultGreetingMutation.Field()

schema = graphene.Schema(query=QueryRootType, mutation=MutationRootType)

graphql_application.config['graphql_schema'] = schema
graphql_application.config['graphql_pretty'] = True


class TestGraphQLHandler(BaseTest):
    def setUp(self):
        BaseTest.setUp(self)

        self.app = webtest.TestApp(graphql_application)

    def testPOST_noSchema_returns500(self):
        graphql_application = webapp2.WSGIApplication([
            ('/graphql', GraphQLHandler)
        ])

        app = webtest.TestApp(graphql_application)
        response = app.post('/graphql', expect_errors=True)
        self.assertEqual(response.status_int, 500)
        self.assertEqual(response.json_body['errors'][0]['message'], 'GraphQL Schema is missing.')

    def testPOST_noInput_returns400(self):
        response = self.app.post('/graphql', expect_errors=True)
        self.assertEqual(response.status_int, 400)

    def testPost_supports_operation_name(self):
        response = self.app.post('/graphql', params=json.dumps(dict(
            query='''
                query helloYou { greet(who: "You"), ...shared }
                query helloWorld { greet(who: "World"), ...shared }
                query helloDolly { greet(who: "Dolly"), ...shared }
                fragment shared on QueryRootType {
                    shared: greet(who: "Everyone")
                }
            ''',
            operation_name='helloDolly'
        )))

        response_dict = json.loads(response.body)
        self.assertDictEqual(
            response_dict.get('data'),
            {
                'greet': 'Hello Dolly!',
                'shared': 'Hello Everyone!'
            }
        )

    def testPOST_support_json_variables(self):
        response = self.app.post('/graphql', params=json.dumps(dict(
            query='query helloWho($who: String){ greet(who: $who) }',
            variables={'who': "ekampf"}
        )))

        response_dict = json.loads(response.body)
        self.assertDictEqual(
            response_dict.get('data'), {'greet': 'Hello ekampf!'}
        )

    def testPOST_reports_argument_validation_errors(self):
        response = self.app.post('/graphql', expect_errors=True, params=json.dumps(dict(
            query='''
                query helloYou { greet(who: 123), ...shared }
                query helloWorld { greet(who: "World"), ...shared }
                query helloDolly { greet(who: "Dolly"), ...shared }
                fragment shared on Query {
                    shared: greet(who: "Everyone")
                }
            ''',
            operation_name='helloYou'
        )))

        self.assertEqual(response.status_int, 400)

        response_dict = json.loads(response.body)
        self.assertEqual(response_dict["errors"][0]["message"], "Argument \"who\" has invalid value 123.\nExpected type \"String\", found 123.")

    def testPOST_reports_missing_operation_name(self):
        response = self.app.post('/graphql', expect_errors=True, params=json.dumps(dict(
            query='''
                query helloWorld { greet(who: "World"), ...shared }
                query helloDolly { greet(who: "Dolly"), ...shared }
                fragment shared on QueryRootType {
                    shared: greet(who: "Everyone")
                }
            '''
        )))

        self.assertEqual(response.status_int, 400)

        response_dict = json.loads(response.body)
        self.assertEqual(response_dict["errors"][0]["message"], "Must provide operation name if query contains multiple operations.")

    def testPOST_handles_syntax_errors(self):
        response = self.app.post('/graphql', expect_errors=True, params=json.dumps(dict(query='syntaxerror')))

        self.assertEqual(response.status_int, 400)

        expected = {
            'errors': [{'locations': [{'column': 1, 'line': 1}],
                        'message': 'Syntax Error GraphQL request (1:1) '
                                   'Unexpected Name "syntaxerror"\n\n1: syntaxerror\n   ^\n'}]
        }
        response_dict = json.loads(response.body)
        self.assertEqual(response_dict, expected)

    def testPOST_handles_poorly_formed_variables(self):
        response = self.app.post('/graphql', expect_errors=True, params=json.dumps(dict(
            query='query helloWho($who: String){ greet(who: $who) }',
            variables='who:You'
        )))

        response_data = json.loads(response.body)
        self.assertEqual(response.status_int, 400)
        self.assertEqual(response_data['errors'][0]['message'], 'Variables are invalid JSON.')

    def testPOST_mutations(self):
        response = self.app.post('/graphql',
                                 json.dumps(
                                     dict(
                                         query='''
                                         mutation TestMutatio  {
                                            changeDefaultGreeting(input: { value: "universe" } ) {
                                                ok,
                                                defaultGreeting
                                            }
                                        }'''
                                     )
                                 ))

        self.assertEqual('universe', response.json_body['data']['changeDefaultGreeting']['defaultGreeting'])
        self.assertEqual(True, response.json_body['data']['changeDefaultGreeting']['ok'])

    def testPOST_override_pretty_via_query_param(self):
        response = self.app.post('/graphql?pretty=true', params=json.dumps(dict(
            query='query helloYou { greet(who: "You") }'
        )))
        self.assertEqual(response.body, '{\n  "data": {\n    "greet": "Hello You!"\n  }\n}')

    def testPOST_override_pretty_via_post_param(self):
        response = self.app.post('/graphql', params=json.dumps(dict(
            query='query helloYou { greet(who: "You") }',
            pretty=True
        )))
        self.assertEqual(response.body, '{\n  "data": {\n    "greet": "Hello You!"\n  }\n}')

    def testPOST_stringBody_readsQueryFromBodyAndRestFromGET(self):
        response = self.app.post('/graphql?pretty=True', params='query helloYou { greet(who: "You") }')
        self.assertEqual(response.body, '{\n  "data": {\n    "greet": "Hello You!"\n  }\n}')

