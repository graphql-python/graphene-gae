import logging
import json
import webapp2
import six

from graphql import GraphQLError, format_error as format_graphql_error

__author__ = 'ekampf'


class GraphQLHandler(webapp2.RequestHandler):
    def post(self):
        schema = self._get_schema()
        pretty = self._get_pretty()

        if not schema:
            webapp2.abort(500, detail='GraphQL Schema is missing.')

        query, operation_name, variables, pretty_override = self._get_grapl_params()
        pretty = pretty if not pretty_override else pretty_override

        result = schema.execute(query,
                                operation_name=operation_name,
                                variable_values=variables,
                                context_value=self._get_context(),
                                root_value=self._get_root_value())

        response = {}
        if result.errors:
            response['errors'] = [self.__format_error(e) for e in result.errors]
            logging.warn("Request had errors: %s", response)
            self._handle_graphql_errors(result.errors)

        if result.invalid:
            logging.error("GraphQL request is invalid: %s", response)
            return self.failed_response(400, response, pretty=pretty)

        response['data'] = result.data
        return self.successful_response(response, pretty=pretty)

    def handle_exception(self, exception, debug):
        logging.exception(exception)

        status_code = 500
        if isinstance(exception, webapp2.HTTPException):
            status_code = exception.code

        self.failed_response(status_code, {
            'errors': [self.__format_error(exception)]
        })

    def _handle_graphql_errors(self, result):
        pass

    def _get_schema(self):
        return self.app.config.get('graphql_schema')

    def _get_pretty(self):
        return self.app.config.get('graphql_pretty', False)

    def _get_grapl_params(self):
        try:
            request_data = self.request.json_body
            if isinstance(request_data, basestring):
                request_data = dict(query=request_data)
        except:
            request_data = {}

        request_data.update(dict(self.request.GET))

        query = request_data.get('query', self.request.body)
        if not query:
            webapp2.abort(400, "Query is empty.")

        operation_name = request_data.get('operation_name')
        variables = request_data.get('variables')
        if variables and isinstance(variables, six.text_type):
            try:
                variables = json.loads(variables)
            except:
                raise webapp2.abort(400, 'Variables are invalid JSON.')

        pretty = request_data.get('pretty')

        return query, operation_name, variables, pretty

    def _get_root_value(self):
        return None

    def _get_context(self):
        return self.request

    def __format_error(self, error):
        if isinstance(error, GraphQLError):
            return format_graphql_error(error)

        return {'message': str(error)}

    def __json_encode(self, data, pretty=False):
        if pretty:
            return json.dumps(data, indent=2, sort_keys=True, separators=(',', ': '))

        return json.dumps(data)

    def successful_response(self, data, pretty=False):
        serialized_data = self.__json_encode(data, pretty=pretty)

        self.response.set_status(200, 'Success')
        self.response.md5_etag()
        self.response.content_type = 'application/json'
        self.response.out.write(serialized_data)

    def failed_response(self, error_code, data, pretty=False):
        serialized_data = self.__json_encode(data, pretty=pretty)

        self.response.set_status(error_code)
        self.response.content_type = 'application/json'
        self.response.out.write(serialized_data)


graphql_application = webapp2.WSGIApplication([
    ('/graphql', GraphQLHandler)
])
