import json
import sys
import os
import warnings

from pymongo import MongoClient
from sklearn.cross_decomposition import PLSRegression

import pandas as pd
import numpy as np

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
            if not feature in item:
                print("Warning: feature {} not present in record, skipping".format(feature))
                break
            rowhash[feature] = item[feature]
        row = pd.DataFrame(rowhash, index=[key])
        # the following is bad in R but maybe ok in python?
        # we should check performance/mem usage....
        dfr = dfr.append(row) # pylint: disable=redefined-variable-type
    dfr.sort_index(inplace=True)
    return dfr


def display_result(inputdata, data_frame, row_wise=True):
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
    if row_wise:
        labels = data_frame.index.tolist()
    else:
        labels = data_frame.columns.tolist()
    output = []
    assert len(labels) == len(inputdata)
    for idx, item in enumerate(inputdata):
        hsh = {"id": labels[idx], "value": item}
        output.append(hsh)
    return output


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

    # does clin_df have any NAs in it? If so, remove those rows:
    rows_to_drop =  clin_df[clin_df.isnull().any(axis=1)].index.tolist()
    clin_df.dropna(inplace=True) # just drop them in one go from clin_df


    # Then remove the corresponding rows from mol_df:
    mol_df.drop(rows_to_drop, inplace=True)

    # Will mol_df ever have NAs in it? TODO find out...

    error = None
    warning = []
    # TODO Handle errors here...
    # make sure that we still have rows in the data frames!
    if not len(mol_df.index):
        error = "No non-NA rows in molecular input"
    if not len(clin_df.index):
        error = "No non-NA rows in clinical input"

    def custom_warn_function(message, *args): # pylint: disable=unused-argument
        """Catch warnings thrown by pls2.fit()"""
        warning.append(str(message))
        print("We got a warning! {}".format(message))

    old_showwarning = warnings.showwarning
    warnings.showwarning = custom_warn_function
    if error:
        print("There's an error, skipping pls2.fit()...")
    else:
        try:
            pls2.fit(mol_df, clin_df)
        except Exception as exc: # pylint: disable=broad-except
            error = str(exc)

    warnings.showwarning = old_showwarning

    if not error and np.all(np.isnan(pls2.x_scores_)): # all x_scores_ values are NAN
        error = "results are NaN; too few rows in input?"


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
        ret2 = {"x_scores": display_result(pls2.x_scores_.tolist(), mol_df),
                "y_scores": display_result(pls2.y_scores_.tolist(), clin_df),
                "x.loadings": display_result(pls2.x_loadings_.tolist(), mol_df,
                                             False),
                "y.loadings": display_result(pls2.y_loadings_.tolist(), clin_df,
                                             False),
                # not 100% sure about this:
                "metadata": display_result(pls2.coef_.tolist(), mol_df, False)}
        ret_obj.update(ret2)
        if warning:
            ret_obj['warning'] = warning

    if os.getenv("PLSR_DEBUG"):
        import IPython;IPython.embed()
    return ret_obj

def main():
    if len(sys.argv) > 1:
        json_filename = sys.argv[1]
    else:
        json_filename = "sample_input2.json"
    with open(json_filename) as jsonfile:
        input_data = json.load(jsonfile)
    plsr_wrapper(**input_data) # ignoring return value...


if __name__ == '__main__':
    main()
