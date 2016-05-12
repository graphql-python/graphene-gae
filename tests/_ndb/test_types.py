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


class QueryRoot(graphene.ObjectType):
    articles = graphene.List(ArticleType)

    @graphene.resolve_only_args
    def resolve_articles(self):
        return Article.query()


schema.query = QueryRoot

class TestNDBTypes(BaseTest):

    def test_objecttype_instanciation(self):
        instance = Article(headline="test123")
        h = ArticleType(instance)
        self.assertEqual(instance.key, h.key)
        self.assertEqual(instance.headline, h.headline)

    def test_query_list(self):
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

    def test_query_repeatedProperty(self):
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


