"""
See the README for information on how to run this app.
"""

import json

from flask import Flask, jsonify, request, Response
from flask_restful import Resource, Api

from plsr_wrapper import PLSRWrapper
from pca_wrapper import PCAWrapper
from distance_wrapper import DistanceWrapper

app = Flask(__name__) # pylint: disable=invalid-name
api = Api(app) # pylint: disable=invalid-name

def post_factory(algorithm_class):
    """create post methods based on algorithm class"""
    def post(self): # pylint: disable=no-self-use,unused-argument
        """Closure for POST method"""
        json_data = request.get_json(force=True)
        expected_keys = algorithm_class.get_input_parameters()
        if not sorted(json_data.keys()) == expected_keys:
            error = "missing key(s): input must contain all of: {}"
            jstr = json.dumps(dict(reason=error.format(expected_keys)))
            resp = Response(jstr,
                            status=400, mimetype='application/json')
            return resp
        result = algorithm_class(**json_data).run_algorithm()

        return jsonify(result)
    return post

# dynamically create resource classes using a closure from post_factory()
PLSRResource = type("PLSRResource", (Resource,),
                    {"post": post_factory(PLSRWrapper)})
PCAResource = type("PCAResource", (Resource,),
                   {"post": post_factory(PCAWrapper)})
DistanceResource = type("DistanceResource", (Resource,),
                   {"post": post_factory(DistanceWrapper)})

# map endpoints to resource classes
api.add_resource(PLSRResource, '/plsr')
api.add_resource(PCAResource, '/pca')
api.add_resource(DistanceResource, '/distance')

if __name__ == '__main__':
    app.run(port=8000) # don't run me this way, see README
