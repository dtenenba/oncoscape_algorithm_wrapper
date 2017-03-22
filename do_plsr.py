import json
import sys
import os

from pymongo import MongoClient
# import jsonpickle

# import numpy as np
import pandas as pd

# TODO - add connection pooling
MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    print("MONGO_URL is not defined in environment.")
    print("See the file setup_env.sh.example for more information.")
    print("Exiting.")
    sys.exit(1)
CLIENT = MongoClient(MONGO_URL)
db = CLIENT.tcga

class InputParameters(object):

    clinical_collection_name = None
    clinical_collection = None
    clinical_data = None
    molecular_collection_name = None
    molecular_data = None
    geneset_list = None
    pt_low = None
    pt_high = None


    def __init__(self, disease, mol_type, geneset, clinical):
        self.disease = disease
        self.mol_type = mol_type
        self.geneset = geneset
        self.clinical = clinical

    def do_plsr(self):
        self.clinical_collection_name = lookup_disease(self.disease)
        self.clinical_collection = db[self.clinical_collection_name]
        # self.clinical_data = self.clinical_collection.find()
        if self.geneset is not "All Genes":
            self.geneset_list = lookup_geneset(self.geneset)
        self.molecular_collection_name = \
            lookup_molecular_collection(self.mol_type, self.disease)
        self.molecular_data = self.get_molecular_data()
        # TODO handle errors here:
        self.pt_low = self.find_extremes()
        self.pt_high = self.find_extremes(False)
        # import IPython;IPython.embed()
        # # FIXME this takes 1m11s! (with All Genes; 2.7s w/Glioma Markers) :
        # md = []
        # for item in self.molecular_data:
        #     md.append(item)
        # print(len(md))
        # import IPython;IPython.embed()
        print(lookup_disease('brain'))

    def get_samplemap(self):
        sample_map = db['kirp_samplemap'].find_one()
        # do mapping...
        return sample_map

    def find_extremes(self, low=True):
        if low:
            operator = "$lt"
            lohi = "below"
        else:
            operator = "$gt"
            lohi = "above"
        query = {}
        for attribute in self.clinical:
            value = attribute.low if low else attribute.high
            query[attribute.field] = {operator: value}
        cursor = db[self.clinical_collection_name].find(query)
        ret = []
        for item in cursor:
            ret.append(item)
        if not ret:
            return Error("No patients {} threshold".format(lohi))
        return ret

    def get_molecular_data(self):
        projection = {"id": 1, "data": 1}
        if self.geneset_list is None:
            # FIXME parallelize this
            return db[self.molecular_collection_name].find({}, projection)
        # first naive iteration:
        return db[self.molecular_collection_name].find(\
            {'id': {'$in': self.geneset_list}}, projection)
        # TODO - use something like this:
        # http://stackoverflow.com/a/38011531/470769


class Clinical(object):

    def __init__(self, field, low, high):
        self.field = field
        self.low = low
        self.high = high


class Error(object):

    def __init__(self, message):
        ret = json.dumps(dict(scores=None, reason=message))
        print(ret)



def lookup_disease(disease):
    lookup = db.lookup_oncoscape_datasources
    res = lookup.find_one({"disease": disease},
                          projection={"clinical.patient" : 1})
    if res is None:
        return None
    return res['clinical']['patient']

def lookup_geneset(geneset):
    lookup = db.lookup_genesets
    res = lookup.find_one({"name": geneset},
                          projection={"genes": 1})
    if res is None:
        return None
    return res['genes']

def convert_mol_result_to_data_frame(mol_result):
    # dict comprehension style:
    # interm = {item['id']: pd.Series(item['data'].values(),
    #                                 index=item['data'].keys()) for item in res}
    # df = pd.DataFrame(interm)
    tmp = {}
    for item in mol_result:
        tmp[item['id']] = pd.Series(item['data'].values(),
                                    index=item['data'].keys())
    return pd.DataFrame(tmp)

def lookup_molecular_collection(mol_type, disease):
    lookup = db.lookup_oncoscape_datasources
    res = lookup.find({"disease": disease, "molecular.type": mol_type},
                      projection={"molecular.collection": 1,
                                   "molecular.type": 1})
    for item in res:
        for mol in item['molecular']:
            if mol['type'] == mol_type:
                return mol['collection']
    return None


def plsr_wrapper(disease, genes, samples, features,
                 molecular_collection, clinical_collection, n_components):
    print("hi")
    return {'hello': 'worldd'}


def main():
    if len(sys.argv) == 1:
        # FIXME change geneset back to 'All Genes'
        clin = [Clinical("days_to_death", 24, 50),
                    Clinical("age_at_diagnosis", 45, 70)]
        input_params = InputParameters("brain", "copy number (gistic2)",
                                       "All Genes", clin)
    else:
        with open(sys.argv[1]) as f:
            input_json = json.load(f)
        # TODO deserialize InputParameters object from json file
        # input_params = jsonpickle.decode(input_json)
    # input_json = '{"disease": "brain", "geneset": "All Genes", "clinical": [{"field": "days_to_death", "py/object": "__main__.Clinical", "high": 50, "low": 15}, {"field": "age_at_diagnosis", "py/object": "__main__.Clinical", "high": 90, "low": 45}], "py/object": "__main__.InputParameters", "molecular_collection_name": null, "clinical_collection_name": null, "mol_type": "copy number (gistic2)"}'
    # input_params = jsonpickle.decode(input_json) # creates an InputParameters instance
    input_params.do_plsr()
    # import IPython;IPython.embed()




if __name__ == '__main__':
    main()

    """
{
   disease: "brain",
   clinical : [
        { field: "days_to_death"
            thresholds: [15, 50]
        },
        { field: "age_at_diagnosis"
            thresholds: [45, 90]
        }
   ],
   geneset: "All Genes",
   mol_type :"gene expression (AffyU133a)"

   Actually mol_type should maybe be:

   copy number (gistic2)
}

In brain_dashboard, without any gene constraints (geneset == 'All Genes'),
the max days_to_death is null (!) (lowest non-null value is 3) and the max days_to_death is 4445.
The min age_at_diagnosis is 10 and the max age_at_diagnosis is 89.
TODO: Let Lisa know that there are records with null days_to_death values.
as of 3/14/2017.
    """
