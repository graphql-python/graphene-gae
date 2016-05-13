from tests.base_test import BaseTest

import graphene

from graphene_gae import NdbObjectType
from tests.models import Tag, Comment, Article

__author__ = 'ekampf'

schema = graphene.Schema()


@schema.register
class TagType(NdbObjectType):
    class Meta:
        model = Tag


@schema.register
class CommentType(NdbObjectType):
    class Meta:
        model = Comment


@schema.register
class ArticleType(NdbObjectType):
    class Meta:
        model = Article
        exclude_fields = ['to_be_excluded']


class QueryRoot(graphene.ObjectType):
    articles = graphene.List(ArticleType)

    @graphene.resolve_only_args
    def resolve_articles(self):
        return Article.query()


schema.query = QueryRoot


class TestNDBTypes(BaseTest):

    def testNdbObjectType_instanciation(self):
        instance = Article(headline="test123")
        h = ArticleType(instance)
        self.assertEqual(h._root, instance)
        self.assertEqual(instance.key, h.key)
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


