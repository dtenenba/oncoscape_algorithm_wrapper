"""
To start this app during local development, run the following:

FLASK_APP=flask_app.py FLASK_DEBUG=1 flask run -p 8000

To call the app with some sample data, run this (from another
window in this same directory):

curl -vX POST http://localhost:8000/plsr -d @sample_input2.json  --header "Content-Type: application/json"

To run this app in a 'production' context, run:

./run.sh

To run it inside a Docker container, see the README.

"""

import json

from flask import Flask, jsonify, request, Response
from flask_restful import Resource, Api

import do_plsr
app = Flask(__name__)
api = Api(app)



class DoPLSR(Resource):
    def post(self):
        # The force arg ignores content type, otherwise a
        # Content-Type: application/json
        # header must be present in the request.
        json_data = request.get_json(force=True)
        expected_keys = ['disease', 'genes', 'samples', 'features',
                         'molecular_collection', 'clinical_collection',
                         'n_components']
        if not sorted(json_data.keys()) == sorted(expected_keys):
            error = "missing key(s): input must contain all of: {}"
            jstr = json.dumps(dict(reason=error.format(expected_keys)))
            resp = Response(jstr,
                            status=400, mimetype='application/json')
            return resp
        result = do_plsr.plsr_wrapper(**json_data)

        return jsonify(result)

api.add_resource(DoPLSR, '/plsr')

if __name__ == '__main__':
    app.run(port=8000)
