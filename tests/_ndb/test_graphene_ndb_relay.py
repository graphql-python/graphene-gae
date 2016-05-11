from tests.base_test import BaseTest

__author__ = 'ekampf'

import graphene
from graphene import relay
from graphene_gae import NdbNode, NdbConnection

from tests.models import Tag, Comment, Article

schema = graphene.Schema()

@schema.register
class TagType(NdbNode):
    class Meta:
        model = Tag

@schema.register
class CommentType(NdbNode):
    class Meta:
        model = Comment

@schema.register
class ArticleType(NdbNode):
    class Meta:
        model = Article

    comments = relay.ConnectionField(CommentType, connection_type=NdbConnection)

    def resolve_comments(self,  args, info):
        return Comment.query(ancestor=self.key)


class QueryRoot(graphene.ObjectType):
    articles = relay.ConnectionField(ArticleType, connection_type=NdbConnection)

    def resolve_articles(self, args, info):
        return Article.query()


schema.query = QueryRoot


class TestGrapheneNDBRelay(BaseTest):

    def test_connectionField(self):
        a1 = Article(headline="Test1", summary="1").put()
        a2 = Article(headline="Test2", summary="2").put()
        a3 = Article(headline="Test3", summary="3").put()

        c1 = Comment(parent=a1, body="c1").put()
        c2 = Comment(parent=a2, body="c2").put()
        c3 = Comment(parent=a3, body="c3").put()

        result = schema.execute("""
            query Articles {
                articles(first:2) {
                    edges {
                        cursor,
                        node {
                            headline,
                            summary,
                            comments {
                                edges {
                                    cursor,
                                    node {
                                        body
                                    }
                                }
                            }
                        }
                    }

                }
            }
            """)

        self.assertEmpty(result.errors)

        articles = result.data.get('articles', {}).get('edges')
        self.assertLength(articles, 2)

        for articleNode in articles:
            article = articleNode['node']
            self.assertLength(article.keys(), 3)
            self.assertIsNotNone(article.get('headline'))
            self.assertIsNotNone(article.get('summary'))

            comments  = article['comments']['edges']
            self.assertLength(comments, 1)
            self.assertEqual(comments[0]['node']['body'], "c" + article['summary'])


    def test_connectionField_empty(self):
        a1 = Article(headline="Test1", summary="1").put()

        result = schema.execute("""
            query Articles {
                articles {
                    edges {
                        cursor,
                        node {
                            headline,
                            createdAt,
                            comments {
                                edges {
                                    node {
                                        body
                                    }
                                }
                            }
                        }
                    }

                }
            }
            """)

        articles = result.data.get('articles', {}).get('edges')
        self.assertLength(articles, 1)

        article = articles[0]['node']
        self.assertLength(article.keys(), 3)
        self.assertIsNotNone(article.get('headline'))
        self.assertIsNotNone(article.get('createdAt'))

        comments = article['comments']['edges']
        self.assertEmpty(comments)
