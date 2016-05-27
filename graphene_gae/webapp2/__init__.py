import logging
import json
import webapp2

from graphql import GraphQLError, format_error as format_graphql_error

__author__ = 'ekampf'


class GraphQLHandler(webapp2.RequestHandler):
    def post(self):
        schema = self.app.config.get('graphql_schema')
        pretty = self.app.config.get('graphql_pretty', True)

        if not schema:
            webapp2.abort(500, detail='GraphQL Schema is missing.')

        query = None if not self.request.body else self.request.json_body.get('query')
        if not query:
            return self.failed_response(400, dict(errors=[dict(message='Query is empty.')]), pretty=pretty)

        operation_name = self.request.json_body.get('operation_name')
        variables = self.request.json_body.get('variables')

        logging.debug("Executing query: %s", query)

        result = schema.execute(query,
                                operation_name=operation_name,
                                variable_values=variables,
                                context_value=self._get_context(),
                                root_value=self._get_root_value())

        response = {}
        if result.errors:
            response['errors'] = [self.__format_error(e) for e in result.errors]

        if result.invalid:
            return self.failed_response(400, response, pretty=pretty)

        response['data'] = result.data
        return self.successful_response(response)

    def _get_root_value(self):
        return None

    def _get_context(self):
        return self.request

    def __format_error(self, error):
        if isinstance(error, GraphQLError):
            return format_graphql_error(error)

        return {'message': str(error)}

    def __json_encode(self, data, pretty=True):
        if pretty:
            return json.dumps(data, indent=2, sort_keys=True, separators=(',', ': '))

        return json.dumps(data)

    def successful_response(self, data, pretty=True):
        serialized_data = self.__json_encode(data, pretty=pretty)

        self.response.set_status(200, 'Success')
        self.response.md5_etag()
        self.response.content_type = 'application/json'
        self.response.out.write(serialized_data)

    def failed_response(self, error_code, data, pretty=True):
        serialized_data = self.__json_encode(data, pretty=pretty)

        self.response.set_status(error_code)
        self.response.content_type = 'application/json'
        self.response.out.write(serialized_data)


graphql_application = webapp2.WSGIApplication([
    ('/graphql', GraphQLHandler)
])
