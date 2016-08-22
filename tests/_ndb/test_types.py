from graphql_relay import to_global_id

from tests.base_test import BaseTest

import graphene

from graphene_gae import NdbObjectType
from tests.models import Tag, Comment, Article, Address, Author, PhoneNumber

__author__ = 'ekampf'


class AddressType(NdbObjectType):
    class Meta:
        model = Address


class PhoneNumberType(NdbObjectType):
    class Meta:
        model = PhoneNumber


class AuthorType(NdbObjectType):
    class Meta:
        model = Author


class TagType(NdbObjectType):
    class Meta:
        model = Tag


class CommentType(NdbObjectType):
    class Meta:
        model = Comment


class ArticleType(NdbObjectType):
    class Meta:
        model = Article
        exclude_fields = ['to_be_excluded']


class QueryRoot(graphene.ObjectType):
    articles = graphene.List(ArticleType)

    @graphene.resolve_only_args
    def resolve_articles(self):
        return Article.query()


schema = graphene.Schema(query=QueryRoot)


class TestNDBTypes(BaseTest):

    def testNdbObjectType_instanciation(self):
        instance = Article(headline="test123")
        h = ArticleType(**instance.to_dict(exclude=["tags", "author_key"]))
        self.assertEqual(instance.headline, h.headline)

    def testNdbObjectType_should_raise_if_no_model(self):
        with self.assertRaises(Exception) as context:
            class Character1(NdbObjectType):
                pass

        assert 'model in the Meta' in str(context.exception.message)

    def testNdbObjectType_should_raise_if_model_is_invalid(self):
        with self.assertRaises(Exception) as context:
            class Character2(NdbObjectType):
                class Meta:
                    model = 1

        assert 'not an NDB model' in str(context.exception.message)

    # def testNdbObjectType_keyProperty_kindDoesntExist_raisesException(self):
    #     with self.assertRaises(Exception) as context:
    #         class ArticleType(NdbObjectType):
    #             class Meta:
    #                 model = Article
    #                 only_fields = ('prop',)
    #
    #             prop = NdbKeyReferenceField('foo', 'bar')
    #
    #         class QueryType(graphene.ObjectType):
    #             articles = graphene.List(ArticleType)
    #
    #             @graphene.resolve_only_args
    #             def resolve_articles(self):
    #                 return Article.query()
    #
    #         schema = graphene.Schema(query=QueryType)
    #         schema.execute('query test {  articles { prop } }')
    #
    #     self.assertIn("Model 'bar' is not accessible by the schema.", str(context.exception.message))

    # def testNdbObjectType_keyProperty_stringRepresentation_kindDoesntExist_raisesException(self):
    #     with self.assertRaises(Exception) as context:
    #         class ArticleType(NdbObjectType):
    #             class Meta:
    #                 model = Article
    #                 only_fields = ('prop',)
    #
    #             prop = NdbKeyStringField('foo', 'bar')
    #
    #         class QueryType(graphene.ObjectType):
    #             articles = graphene.List(ArticleType)
    #
    #             @graphene.resolve_only_args
    #             def resolve_articles(self):
    #                 return Article.query()
    #
    #         schema = graphene.Schema(query=QueryType)
    #         schema.execute('query test {  articles { prop } }')
    #
    #     self.assertIn("Model 'bar' is not accessible by the schema.", str(context.exception.message))

    def testQuery_excludedField(self):
        Article(headline="h1", summary="s1").put()

        class ArticleType(NdbObjectType):
            class Meta:
                model = Article
                exclude_fields = ['summary']

        class QueryType(graphene.ObjectType):
            articles = graphene.List(ArticleType)

            @graphene.resolve_only_args
            def resolve_articles(self):
                return Article.query()

        schema = graphene.Schema(query=QueryType)
        query = '''
            query ArticlesQuery {
              articles { headline, summary }
            }
        '''

        result = schema.execute(query)

        self.assertIsNotNone(result.errors)
        self.assertTrue('Cannot query field "summary"' in result.errors[0].message)

    def testQuery_onlyFields(self):
        Article(headline="h1", summary="s1").put()

        class ArticleType(NdbObjectType):
            class Meta:
                model = Article
                only_fields = ['headline']

        class QueryType(graphene.ObjectType):
            articles = graphene.List(ArticleType)

            @graphene.resolve_only_args
            def resolve_articles(self):
                return Article.query()

        schema = graphene.Schema(query=QueryType)
        query = '''
                    query ArticlesQuery {
                      articles { headline }
                    }
                '''

        result = schema.execute(query)

        self.assertIsNotNone(result.data)
        self.assertEqual(result.data['articles'][0]['headline'], 'h1')

        query = '''
                    query ArticlesQuery {
                      articles { headline, summary }
                    }
                '''
        result = schema.execute(query)

        self.assertIsNotNone(result.errors)
        self.assertTrue('Cannot query field "summary"' in result.errors[0].message)

    def testQuery_list(self):
        Article(headline="Test1", summary="1").put()
        Article(headline="Test2", summary="2").put()
        Article(headline="Test3", summary="3").put()

        result = schema.execute("""
            query Articles {
                articles {
                    headline
                }
            }
        """)
        self.assertEmpty(result.errors)

        self.assertLength(result.data['articles'], 3)

        for article in result.data['articles']:
            self.assertLength(article.keys(), 1)
            self.assertEqual(article.keys()[0], 'headline')

    def testQuery_repeatedProperty(self):
        keywords = ["a", "b", "c"]
        a = Article(headline="Test1", keywords=keywords).put()

        result = schema.execute("""
            query Articles {
                articles {
                    headline,
                    keywords,
                    createdAt
                }
            }
        """)
        self.assertEmpty(result.errors)

        self.assertLength(result.data['articles'], 1)

        article = result.data['articles'][0]
        self.assertEqual(article["createdAt"], str(a.get().created_at.isoformat()))
        self.assertEqual(article["headline"], "Test1")
        self.assertListEqual(article["keywords"], keywords)

    def testQuery_structuredProperty(self):
        mobile = PhoneNumber(area="650", number="12345678")
        author_key = Author(name="John Dow", email="john@dow.com", mobile=mobile).put()
        Article(headline="Test1", author_key=author_key).put()

        result = schema.execute("""
            query Articles {
                articles {
                    headline,
                    authorId
                    author {
                        name
                        email
                        mobile { area, number }
                    }
                }
            }
        """)
        self.assertEmpty(result.errors, msg=str(result.errors))

        article = result.data['articles'][0]
        self.assertEqual(article["headline"], "Test1")

        author = article['author']
        self.assertEqual(author["name"], "John Dow")
        self.assertEqual(author["email"], "john@dow.com")
        self.assertDictEqual(dict(area="650", number="12345678"), dict(author["mobile"]))

    def testQuery_structuredProperty_repeated(self):
        address1 = Address(address1="address1", address2="apt 1", city="Mountain View")
        address2 = Address(address1="address2", address2="apt 2", city="Mountain View")
        author_key = Author(name="John Dow", email="john@dow.com", addresses=[address1, address2]).put()
        Article(headline="Test1", author_key=author_key).put()

        result = schema.execute("""
            query Articles {
                articles {
                    headline,
                    author {
                        name
                        email
                        addresses {
                            address1
                            address2
                            city
                        }
                    }
                }
            }
        """)
        self.assertEmpty(result.errors)

        article = result.data['articles'][0]
        self.assertEqual(article["headline"], "Test1")

        author = article['author']
        self.assertEqual(author["name"], "John Dow")
        self.assertEqual(author["email"], "john@dow.com")
        self.assertLength(author["addresses"], 2)

        addresses = [dict(d) for d in author["addresses"]]
        self.assertIn(address1.to_dict(), addresses)
        self.assertIn(address2.to_dict(), addresses)

    def testQuery_keyProperty(self):
        author_key = Author(name="john dow", email="john@dow.com").put()
        article_key = Article(headline="h1", summary="s1", author_key=author_key).put()

        result = schema.execute('''
            query ArticleWithAuthorID {
                articles {
                    ndbId
                    headline
                    authorId
                    authorNdbId: authorId(ndb: true)
                    author {
                        name, email
                    }
                }
            }
        ''')

        self.assertEmpty(result.errors)

        article = dict(result.data['articles'][0])
        self.assertEqual(article['ndbId'], str(article_key.id()))
        self.assertEqual(article['authorNdbId'], str(author_key.id()))

        author = dict(article['author'])
        self.assertDictEqual(author, {'name': u'john dow', 'email': u'john@dow.com'})
        self.assertEqual('h1', article['headline'])
        self.assertEqual(to_global_id('AuthorType', author_key.urlsafe()), article['authorId'])

    def testQuery_repeatedKeyProperty(self):
        tk1 = Tag(name="t1").put()
        tk2 = Tag(name="t2").put()
        tk3 = Tag(name="t3").put()
        tk4 = Tag(name="t4").put()
        Article(headline="h1", summary="s1", tags=[tk1, tk2, tk3, tk4]).put()

        result = schema.execute('''
            query ArticleWithAuthorID {
                articles {
                    headline
                    authorId
                    tagIds
                    tags {
                        name
                    }
                }
            }
        ''')

        self.assertEmpty(result.errors)

        article = dict(result.data['articles'][0])
        self.assertListEqual(map(lambda k: to_global_id('TagType', k.urlsafe()), [tk1, tk2, tk3, tk4]), article['tagIds'])

        self.assertLength(article['tags'], 4)
        for i in range(0, 3):
            self.assertEqual(article['tags'][i]['name'], 't%s' % (i + 1))
