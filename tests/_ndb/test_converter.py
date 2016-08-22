import mock

from graphene_gae.ndb.types import NdbObjectType
from tests.base_test import BaseTest

from google.appengine.ext import ndb

import graphene
from graphene import List, NonNull, String
from graphene.types.json import JSONString
from graphene.types.datetime import DateTime

from graphene_gae.ndb.fields import NdbKeyStringField, NdbKeyReferenceField, DynamicNdbKeyStringField, DynamicNdbKeyReferenceField
from graphene_gae.ndb.converter import convert_ndb_property

__author__ = 'ekampf'


class SomeWeirdUnknownProperty(ndb.Property):
    pass


class TestNDBConverter(BaseTest):
    def __assert_conversion(self, ndb_property_type, expected_graphene_type, *args, **kwargs):
        ndb_property = ndb_property_type(*args, **kwargs)
        result = convert_ndb_property(ndb_property)
        graphene_field = result.field
        self.assertEqual(graphene_field._type, expected_graphene_type)

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
        result = convert_ndb_property(ndb_prop)
        graphene_type = result.field._type

        self.assertIsInstance(graphene_type, graphene.List)
        self.assertEqual(graphene_type.of_type, graphene.String)

    def testStringProperty_required_shouldConvertToList(self):
        ndb_prop = ndb.StringProperty(required=True)
        result = convert_ndb_property(ndb_prop)
        graphene_type = result.field._type

        self.assertIsInstance(graphene_type, graphene.NonNull)
        self.assertEqual(graphene_type.of_type, graphene.String)

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

    def testKeyProperty_withSuffix(self):
        class User(ndb.Model):
            name = ndb.StringProperty()

        class UserType(NdbObjectType):
            class Meta:
                model = User

        prop = ndb.KeyProperty(kind='User')
        prop._code_name = 'user_key'

        conversion = convert_ndb_property(prop)

        self.assertLength(conversion, 2)

        self.assertEqual(conversion[0].name, 'user_id')
        self.assertIsInstance(conversion[0].field, DynamicNdbKeyStringField)
        _type = conversion[0].field.get_type()
        self.assertIsInstance(_type, NdbKeyStringField)
        self.assertEqual(_type._type, String)

        self.assertEqual(conversion[1].name, 'user')
        self.assertIsInstance(conversion[1].field, DynamicNdbKeyReferenceField)
        _type = conversion[1].field.get_type()
        self.assertIsInstance(_type, NdbKeyReferenceField)
        self.assertEqual(_type._type, UserType)

    def testKeyProperty_withSuffix_repeated(self):
        class User(ndb.Model):
            name = ndb.StringProperty()

        class UserType(NdbObjectType):
            class Meta:
                model = User

        prop = ndb.KeyProperty(kind='User', repeated=True)
        prop._code_name = 'user_keys'

        conversion = convert_ndb_property(prop)

        self.assertLength(conversion, 2)

        self.assertEqual(conversion[0].name, 'user_ids')
        self.assertIsInstance(conversion[0].field, DynamicNdbKeyStringField)
        _type = conversion[0].field.get_type()
        self.assertIsInstance(_type, NdbKeyStringField)
        self.assertIsInstance(_type._type, List)
        self.assertEqual(_type._type.of_type, String)

        self.assertEqual(conversion[1].name, 'users')
        self.assertIsInstance(conversion[1].field, DynamicNdbKeyReferenceField)
        _type = conversion[1].field.get_type()
        self.assertIsInstance(_type, NdbKeyReferenceField)
        self.assertIsInstance(_type._type, List)
        self.assertEqual(_type._type.of_type, UserType)

    def testKeyProperty_withSuffix_required(self):
        class User(ndb.Model):
            name = ndb.StringProperty()

        class UserType(NdbObjectType):
            class Meta:
                model = User

        prop = ndb.KeyProperty(kind='User', required=True)
        prop._code_name = 'user_key'

        conversion = convert_ndb_property(prop)

        self.assertLength(conversion, 2)

        self.assertEqual(conversion[0].name, 'user_id')
        self.assertIsInstance(conversion[0].field, DynamicNdbKeyStringField)
        _type = conversion[0].field.get_type()
        self.assertIsInstance(_type, NdbKeyStringField)
        self.assertIsInstance(_type._type, NonNull)
        self.assertEqual(_type._type.of_type, String)

        self.assertEqual(conversion[1].name, 'user')
        self.assertIsInstance(conversion[1].field, DynamicNdbKeyReferenceField)
        _type = conversion[1].field.get_type()
        self.assertIsInstance(_type, NdbKeyReferenceField)
        self.assertIsInstance(_type._type, NonNull)
        self.assertEqual(_type._type.of_type, UserType)

    def testKeyProperty_withoutSuffix(self):
        class User(ndb.Model):
            name = ndb.StringProperty()

        class UserType(NdbObjectType):
            class Meta:
                model = User

        prop = ndb.KeyProperty(kind='User')
        prop._code_name = 'user'

        conversion = convert_ndb_property(prop)

        self.assertLength(conversion, 2)

        self.assertEqual(conversion[0].name, 'user_id')
        self.assertIsInstance(conversion[0].field, DynamicNdbKeyStringField)
        _type = conversion[0].field.get_type()
        self.assertIsInstance(_type, NdbKeyStringField)
        self.assertEqual(_type._type, String)

        self.assertEqual(conversion[1].name, 'user')
        self.assertIsInstance(conversion[1].field, DynamicNdbKeyReferenceField)
        _type = conversion[1].field.get_type()
        self.assertIsInstance(_type, NdbKeyReferenceField)
        self.assertEqual(_type._type, UserType)
