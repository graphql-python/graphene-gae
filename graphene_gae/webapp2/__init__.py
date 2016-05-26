import logging
import json
import webapp2
from graphql import GraphQLError

__author__ = 'ekampf'


class GraphQLHandler(webapp2.RequestHandler):
    def post(self):
        schema = self.app.config.get('graphql_schema')
        if not schema:
            webapp2.abort(500, detail='GraphQL Schema is missing.')

        pretty = self.app.config.get('graphql_pretty', True)

        query = self.request.body
        logging.debug("Executing query: %s", query)

        try:
            result = schema.execute(query)
            serialized_result = self.__json_encode(result, pretty=pretty)

            self.response.set_status(200, 'Success')
            self.response.md5_etag()
            self.response.out.write(serialized_result)

        except GraphQLError as gqlex:
            webapp2.abort(400, detail='Failed to execute query: %s' % gqlex.message, comment=str(gqlex))
        except Exception as ex:
            webapp2.abort(400, detail='Failed to execute query', comment=str(ex))

    def __json_encode(self, data, pretty=True):
        if pretty:
            return json.dumps(data, indent=2, sort_keys=True, separators=(',', ': '))

        return json.dumps(data)


graphql_application = webapp2.WSGIApplication([
    ('/graphql', GraphQLHandler)
])
