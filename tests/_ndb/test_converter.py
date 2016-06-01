import mock
from tests.base_test import BaseTest

from google.appengine.ext import ndb

import graphene
from graphene.core.types.custom_scalars import DateTime, JSONString

from graphene_gae.ndb.converter import convert_ndb_property

__author__ = 'ekampf'


class SomeWeirdUnknownProperty(ndb.Property):
    pass


class TestNDBConverter(BaseTest):
    def __assert_conversion(self, ndb_property_type, expected_graphene_type, *args, **kwargs):
        ndb_property = ndb_property_type(*args, **kwargs)
        conversion_result = convert_ndb_property(ndb_property)
        graphene_field_type = conversion_result.field
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
        patch_convert.get.return_value = lambda _, __: None
        with self.assertRaises(Exception) as context:
            prop = ndb.StringProperty()
            prop._code_name = "my_prop"
            convert_ndb_property(prop)

        self.assertTrue("Failed to convert NDB field my_prop" in context.exception.message, msg=context.exception.message)

    def testStringProperty_shouldConvertToString(self):
        self.__assert_conversion(ndb.StringProperty, graphene.String)

    def testStringProperty_repeated_shouldConvertToList(self):
        ndb_prop = ndb.StringProperty(repeated=True)
        conversion_result = convert_ndb_property(ndb_prop)
        graphene_type = conversion_result.field

        self.assertIsInstance(graphene_type, graphene.List)
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

    def testKeyProperty_withSuffixRemoval_removesSuffix(self):
        prop = ndb.KeyProperty()
        prop._code_name = "user_key"

        conversion = convert_ndb_property(prop)
        self.assertEqual(conversion.name, "user")

    def testKeyProperty_repeatedPlural_withSuffixRemoval_removesSuffixAndPluralName(self):
        prop = ndb.KeyProperty()
        prop._code_name = "user_keys"
        conversion = convert_ndb_property(prop)
        self.assertEqual(conversion.name, "users")

        prop = ndb.KeyProperty()
        prop._code_name = "tag_name_keys"
        conversion = convert_ndb_property(prop)
        self.assertEqual(conversion.name, "tag_names")

        prop = ndb.KeyProperty()
        prop._code_name = "person_keys"
        conversion = convert_ndb_property(prop)
        self.assertEqual(conversion.name, "people")

        prop = ndb.KeyProperty()
        prop._code_name = "universal_category_keys"
        conversion = convert_ndb_property(prop)
        self.assertEqual(conversion.name, "universal_categories")
