import logging
import json
import webapp2
from webapp2_extras import jinja2
import six


from graphql import GraphQLError, format_error as format_graphql_error

__author__ = 'ekampf'


class GraphQLHandler(webapp2.RequestHandler):
    def get(self):
        return self._handle_request()

    def post(self):
        return self._handle_request()

    def _handle_request(self):
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
                                root_value=self._get_root_value(),
                                middleware=self._get_middleware())

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

    def _get_middleware(self):
        return None

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


class GraphiqlHandler(webapp2.RequestHandler):
    GRAPHIQL_VERSION = '0.7.1'

    GRAPHIQL_TEMPLATE = '''
    The request to this GraphQL server provided the header "Accept: text/html"
    and as a result has been presented GraphiQL - an in-browser IDE for
    exploring GraphQL.
    If you wish to receive JSON, provide the header "Accept: application/json" or
    add "&raw" to the end of the URL within a browser.
    -->
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        html, body {
          height: 100%;
          margin: 0;
          overflow: hidden;
          width: 100%;
        }
      </style>
      <meta name="referrer" content="no-referrer">
      <link href="//cdn.jsdelivr.net/graphiql/{{graphiql_version}}/graphiql.css" rel="stylesheet" />
      <script src="//cdn.jsdelivr.net/fetch/0.9.0/fetch.min.js"></script>
      <script src="//cdn.jsdelivr.net/react/15.0.0/react.min.js"></script>
      <script src="//cdn.jsdelivr.net/react/15.0.0/react-dom.min.js"></script>
      <script src="//cdn.jsdelivr.net/graphiql/{{graphiql_version}}/graphiql.min.js"></script>
    </head>
    <body>
      <script>
        // Collect the URL parameters
        var parameters = {};
        window.location.search.substr(1).split('&').forEach(function (entry) {
          var eq = entry.indexOf('=');
          if (eq >= 0) {
            parameters[decodeURIComponent(entry.slice(0, eq))] =
              decodeURIComponent(entry.slice(eq + 1));
          }
        });
        // Produce a Location query string from a parameter object.
        function locationQuery(params) {
          return '?' + Object.keys(params).map(function (key) {
            return encodeURIComponent(key) + '=' +
              encodeURIComponent(params[key]);
          }).join('&');
        }
        // Derive a fetch URL from the current URL, sans the GraphQL parameters.
        var graphqlParamNames = {
          query: true,
          variables: true,
          operationName: true
        };
        var otherParams = {};
        for (var k in parameters) {
          if (parameters.hasOwnProperty(k) && graphqlParamNames[k] !== true) {
            otherParams[k] = parameters[k];
          }
        }
        var fetchURL = locationQuery(otherParams);
        // Defines a GraphQL fetcher using the fetch API.
        function graphQLFetcher(graphQLParams) {
          return fetch(fetchURL, {
            method: 'post',
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(graphQLParams),
            credentials: 'include',
          }).then(function (response) {
            return response.text();
          }).then(function (responseBody) {
            try {
              return JSON.parse(responseBody);
            } catch (error) {
              return responseBody;
            }
          });
        }
        // When the query and variables string is edited, update the URL bar so
        // that it can be easily shared.
        function onEditQuery(newQuery) {
          parameters.query = newQuery;
          updateURL();
        }
        function onEditVariables(newVariables) {
          parameters.variables = newVariables;
          updateURL();
        }
        function onEditOperationName(newOperationName) {
          parameters.operationName = newOperationName;
          updateURL();
        }
        function updateURL() {
          history.replaceState(null, null, locationQuery(parameters));
        }
        // Render <GraphiQL /> into the body.
        ReactDOM.render(
          React.createElement(GraphiQL, {
            fetcher: graphQLFetcher,
            onEditQuery: onEditQuery,
            onEditVariables: onEditVariables,
            onEditOperationName: onEditOperationName,
            query: {{ query|tojson }},
            response: {{ result|tojson }},
            variables: {{ variables|tojson }},
            operationName: {{ operation_name|tojson }},
          }),
          document.body
        );
      </script>
    </body>
    </html>
    '''

    @webapp2.cached_property
    def jinja2(self):
        # Returns a Jinja2 renderer cached in the app registry.
        return jinja2.get_jinja2()

    def __render_graphiql(self, graphiql_version=None, graphiql_template=None, **kwargs):
        graphiql_version = graphiql_version or self.GRAPHIQL_VERSION
        graphiql_template = graphiql_template or self.GRAPHIQL_TEMPLATE

        template = self.jinja2.environment.from_string(graphiql_template)
        return template.render(graphiql_version=graphiql_version, **kwargs)

    def get(self):
        query, operation_name, variables, result = self._get_grapl_params()
        vars = dict(query=query, operation_name=operation_name, variables=variables, result=result)

        self.response.write(self.__render_graphiql(**vars))


    def _get_grapl_params(self):
        request_data = self.request.GET

        query = request_data.get('query', '')
        operation_name = request_data.get('operation_name', '')
        variables = request_data.get('variables', '')
        result = request_data.get('result', '')
        return query, operation_name, variables, result


graphql_application = webapp2.WSGIApplication([
    ('/graphql', GraphQLHandler),
    ('/graphiql', GraphiqlHandler),
])
