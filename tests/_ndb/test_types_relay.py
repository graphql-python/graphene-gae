from tests.base_test import BaseTest

import graphene
from graphene_gae import NdbNode, NdbConnectionField

from tests.models import Tag, Comment, Article, Author

__author__ = 'ekampf'


schema = graphene.Schema()


@schema.register
class AuthorType(NdbNode):
    class Meta:
        model = Author


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

    comments = NdbConnectionField(CommentType)

    def resolve_comments(self,  args, info):
        return Comment.query(ancestor=self.key)


class QueryRoot(graphene.ObjectType):
    articles = NdbConnectionField(ArticleType)

    def resolve_articles(self, args, info):
        return Article.query()


schema.query = QueryRoot


class TestNDBTypesRelay(BaseTest):

    def test_keyProperty(self):
        Article(
            headline="Test1",
            summary="1",
            author_key=Author(name="John Dow", email="john@dow.com").put(),
            tags=[
                Tag(name="tag1").put(),
                Tag(name="tag2").put(),
                Tag(name="tag3").put(),
            ]
        ).put()

        result = schema.execute("""
            query Articles {
                articles(first:2) {
                    edges {
                        cursor,
                        node {
                            headline,
                            summary,
                            author { name },
                            tags { name }
                        }
                    }

                }
            }
            """)

        self.assertEmpty(result.errors, msg=str(result.errors))

        articles = result.data.get('articles', {}).get('edges', [])
        self.assertLength(articles, 1)

        article = articles[0]['node']
        self.assertEqual(article['headline'], 'Test1')
        self.assertEqual(article['summary'], '1')

        author = article['author']
        self.assertLength(author.keys(), 1)
        self.assertEqual(author['name'], 'John Dow')

        tags = article['tags']
        tag_names = [t['name'] for t in tags]
        self.assertListEqual(tag_names, ['tag1', 'tag2', 'tag3'])

    def test_connectionField(self):
        a1 = Article(headline="Test1", summary="1").put()
        a2 = Article(headline="Test2", summary="2").put()
        a3 = Article(headline="Test3", summary="3").put()

        Comment(parent=a1, body="c1").put()
        Comment(parent=a2, body="c2").put()
        Comment(parent=a3, body="c3").put()

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

            comments = article['comments']['edges']
            self.assertLength(comments, 1)
            self.assertEqual(comments[0]['node']['body'], "c" + article['summary'])

    def test_connectionField_empty(self):
        Article(headline="Test1", summary="1").put()

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
