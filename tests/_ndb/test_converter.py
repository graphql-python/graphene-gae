import mock
from tests.base_test import BaseTest

from google.appengine.ext import ndb

import graphene
from graphene import List, NonNull
from graphene.types.json import JSONString
from graphene.types.datetime import DateTime

# from graphene_gae.ndb.fields import NdbKeyStringField, NdbKeyField
from graphene_gae.ndb.converter import convert_ndb_property

__author__ = 'ekampf'


class SomeWeirdUnknownProperty(ndb.Property):
    pass


class TestNDBConverter(BaseTest):
    def __assert_conversion(self, ndb_property_type, expected_graphene_type, *args, **kwargs):
        ndb_property = ndb_property_type(*args, **kwargs)
        graphene_field_type = convert_ndb_property(ndb_property)
        self.assertIsInstance(graphene_field_type, expected_graphene_type)

    def testUnknownProperty_raisesException(self):
        with self.assertRaises(Exception) as context:
            prop = SomeWeirdUnknownProperty()
            prop._code_name = "my_prop"
            convert_ndb_property(prop)

        self.assertTrue("Don't know how to convert" in context.exception.message, msg=context.exception.message)

    @mock.patch('graphene_gae.ndb.converter.converters')
    def testNoneResult_raisesException(self, patch_convert):
        from graphene_gae.ndb.converter import convert_ndb_property
        patch_convert.get.return_value = lambda _: None
        with self.assertRaises(Exception) as context:
            prop = ndb.StringProperty()
            prop._code_name = "my_prop"
            convert_ndb_property(prop)

        expected_message = 'Failed to convert NDB propeerty to a GraphQL field my_prop (StringProperty())'
        self.assertTrue(expected_message in context.exception.message, msg=context.exception.message)

    def testStringProperty_shouldConvertToString(self):
        self.__assert_conversion(ndb.StringProperty, graphene.String)

    def testStringProperty_repeated_shouldConvertToList(self):
        ndb_prop = ndb.StringProperty(repeated=True)
        graphene_type = convert_ndb_property(ndb_prop)

        self.assertIsInstance(graphene_type, graphene.List)
        self.assertIsInstance(graphene_type.of_type, graphene.String)

    def testStringProperty_required_shouldConvertToList(self):
        ndb_prop = ndb.StringProperty(required=True)
        graphene_type = convert_ndb_property(ndb_prop)

        self.assertIsInstance(graphene_type, graphene.NonNull)
        self.assertIsInstance(graphene_type.of_type, graphene.String)

    def testTextProperty_shouldConvertToString(self):
        self.__assert_conversion(ndb.TextProperty, graphene.String)

    def testBoolProperty_shouldConvertToString(self):
        self.__assert_conversion(ndb.BooleanProperty, graphene.Boolean)

    def testIntProperty_shouldConvertToString(self):
        self.__assert_conversion(ndb.IntegerProperty, graphene.Int)

    def testFloatProperty_shouldConvertToString(self):
        self.__assert_conversion(ndb.FloatProperty, graphene.Float)

    def testDateProperty_shouldConvertToString(self):
        self.__assert_conversion(ndb.DateProperty, DateTime)

    def testDateTimeProperty_shouldConvertToString(self):
        self.__assert_conversion(ndb.DateTimeProperty, DateTime)

    def testJsonProperty_shouldConvertToString(self):
        self.__assert_conversion(ndb.JsonProperty, JSONString)

    # def testKeyProperty_withSuffix(self):
    #     prop = ndb.KeyProperty()
    #     prop._code_name = 'user_key'
    #
    #     conversion = convert_ndb_property(prop)
    #
    #     self.assertLength(conversion, 2)
    #
    #     self.assertEqual(conversion[0].name, 'user_id')
    #     self.assertIsInstance(conversion[0].field, NdbKeyStringField)
    #
    #     self.assertEqual(conversion[1].name, 'user')
    #     self.assertIsInstance(conversion[1].field, NdbKeyField)
    #
    # def testKeyProperty_withSuffix_repeated(self):
    #     prop = ndb.KeyProperty(repeated=True)
    #     prop._code_name = 'user_keys'
    #
    #     conversion = convert_ndb_property(prop)
    #
    #     self.assertLength(conversion, 2)
    #
    #     self.assertEqual(conversion[0].name, 'user_ids')
    #     self.assertIsInstance(conversion[0].field, List)
    #     self.assertIsInstance(conversion[0].field.of_type, NdbKeyStringField)
    #
    #     self.assertEqual(conversion[1].name, 'users')
    #     self.assertIsInstance(conversion[1].field, List)
    #     self.assertIsInstance(conversion[1].field.of_type, NdbKeyField)
    #
    # def testKeyProperty_withSuffix_required(self):
    #     prop = ndb.KeyProperty(required=True)
    #     prop._code_name = 'user_key'
    #
    #     conversion = convert_ndb_property(prop)
    #
    #     self.assertLength(conversion, 2)
    #
    #     self.assertEqual(conversion[0].name, 'user_id')
    #     self.assertIsInstance(conversion[0].field, NonNull)
    #     self.assertIsInstance(conversion[0].field.of_type, NdbKeyStringField)
    #
    #     self.assertEqual(conversion[1].name, 'user')
    #     self.assertIsInstance(conversion[1].field, NonNull)
    #     self.assertIsInstance(conversion[1].field.of_type, NdbKeyField)
    #
    # def testKeyProperty_withoutSuffix(self):
    #     prop = ndb.KeyProperty()
    #     prop._code_name = 'user'
    #
    #     conversion = convert_ndb_property(prop)
    #
    #     self.assertLength(conversion, 2)
    #
    #     self.assertEqual(conversion[0].name, 'user_id')
    #     self.assertIsInstance(conversion[0].field, NdbKeyStringField)
    #
    #     self.assertEqual(conversion[1].name, 'user')
    #     self.assertIsInstance(conversion[1].field, NdbKeyField)
