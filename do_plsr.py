import json
import sys
import os

from pymongo import MongoClient
from sklearn.cross_decomposition import PLSRegression

import pandas as pd

# TODO - add connection pooling
MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    print("MONGO_URL is not defined in environment.")
    print("See the file setup_env.sh.example for more information.")
    print("Exiting.")
    sys.exit(1)
CLIENT = MongoClient(MONGO_URL)
db = CLIENT.tcga # pylint: disable=invalid-name


def cursor_to_data_frame(cursor):
    dfr = pd.DataFrame()
    for item in cursor:
        key = item['id']
        dfr[key] = pd.Series(list(item['data'].values()),
                             index=list(item['data'].keys()))
    return dfr


def get_data_frame(collection, query=None, projection=None):
    if not query:
        query = {}
    if not projection:
        projection = {}
    cursor = db[collection].find(query, None)
    dfr = cursor_to_data_frame(cursor)
    dfr.sort_index(inplace=True)
    return dfr



def get_projection(items):
    if not items:
        return None
    ret = {}
    for item in items:
        ret[item] = 1
    return ret

def clin_coll_to_df(clinical_collection, disease, # pylint: disable=too-many-locals
                    features, samples):
    mapcol = "{}_samplemap".format(disease)
    sample_pt_map = db[mapcol].find_one()
    if samples:
        wanted_pts = [sample_pt_map[x] for x in samples]
        query = {"patient_ID": {"$in": wanted_pts}}
    else:
        query = {}

    projection = get_projection(features + ["patient_ID"])
    cursor = db[clinical_collection].find(query, projection)
    pt_sample_map = {v: k for k, v in sample_pt_map.items()}

    dfr = pd.DataFrame()
    for item in cursor:
        key = pt_sample_map[item['patient_ID']]
        rowhash = {}
        for feature in features:
            rowhash[feature] = item[feature]
        row = pd.DataFrame(rowhash, index=[key])
        # the following is bad in R but maybe ok in python?
        # we should check performance/mem usage....
        dfr = dfr.append(row) # pylint: disable=redefined-variable-type
    dfr.sort_index(inplace=True)
    return dfr


def display_result(result, data_frame, is_score=True):
    """
    If we call this from inside plsr_wrapper as follows:

    display_result(pls2.x_scores_, mol_df)

    Then we want to output something like that looks like this when
    converted to JSON:

      "x_scores":[
          {
             "id":"TCGA-E1-5319-01",
             "value":[
                -3.1,
                1.5
             ]
          },
          {
             "id":"TCGA-HT-7693-01",
             "value":[
                0.8,
                0.5
             ]
          }
       ]


    """
    # do we handle metadata/coef_ here?
    pass # FIXME implement


def plsr_wrapper(disease, genes, samples, features,
                 molecular_collection, clinical_collection, n_components):

    mol_df = get_data_frame(molecular_collection,
                            {"id": {"$in": genes}})
    if samples: # subset by samples
        subset = [x for x in mol_df.index if x in samples]
        mol_df = mol_df.loc[subset]
    mol_df.sort_index(inplace=True)

    clin_df = clin_coll_to_df(clinical_collection, disease,
                              features, samples)

    # subset clin_df by rows of mol_df
    subset = list(mol_df.index)
    clin_df = clin_df.loc[subset]

    pls2 = PLSRegression(n_components=n_components)

    error = None
    if mol_df.isnull().values.any():
        error = "null values in molecular data"
    if clin_df.isnull().values.any():
        error = "null values in clinical data"

    if not error:
        pls2.fit(mol_df, clin_df)

    # FIXME handle other causes of errors
    # FIXME should numbers be returned with a certain precision?

    ret_obj = {"disease": disease,
               "dataType": "PLSR",
               "score": "sample",
               "x_loading": "hugo",
               "y_loading": "feature",
               "default": False,
               "x_scores": None,
               "y_scores": None,
               "x.loadings": None,
               "y.loadings": None,
               "metadata": None
              }
    if error:
        ret_obj['reason'] = error
    else:
        # FIXME clarify how scores & loadings should be displayed
        ret2 = {"x_scores": pls2.x_scores_.tolist(),
                "y_scores": pls2.y_scores_.tolist(),
                "x.loadings": pls2.x_loadings_.tolist(),
                "y.loadings": pls2.y_loadings_.tolist(),
                # FIXME how should metadata look in returned JSON?
                # Not defined in pseudocode...
                "metadata": pls2.coef_.tolist()}
        ret_obj.update(ret2)


    # import IPython;IPython.embed()
    return ret_obj

def main():
    with open("sample_input2.json") as jsonfile:
        input_data = json.load(jsonfile)
    plsr_wrapper(**input_data) # ignoring return value...


if __name__ == '__main__':
    main()
