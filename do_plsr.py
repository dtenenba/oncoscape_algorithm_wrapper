import config
from pymongo import MongoClient
import jsonpickle

client = MongoClient(config.MONGO_URL)
db = client.tcga

class InputParameters(object):

    def __init__(self, disease, mol_type, geneset, clinical):
        self.disease = disease
        self.mol_type = mol_type
        self.geneset = geneset
        self.clinical = clinical
        self.clinical_collection_name = None
        self.molecular_collection_name = None

    # def __repr__(self):
    #     return str(self.__dict__)


class Clinical(object):

    def __init__(self, field, low, high):
        self.field = field
        self.low = low
        self.high = high

    # def __repr__(self):
    #     return str(self.__dict__)

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


if __name__ == '__main__':
    input_json = '{"disease": "brain", "geneset": "All Genes", "clinical": [{"field": "days_to_death", "py/object": "__main__.Clinical", "high": 50, "low": 15}, {"field": "age_at_diagnosis", "py/object": "__main__.Clinical", "high": 90, "low": 45}], "py/object": "__main__.InputParameters", "molecular_collection_name": null, "clinical_collection_name": null, "mol_type": "copy number (gistic2)"}'
    input = jsonpickle.decode(input_json) # creates an InputParameters instance


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
    """
    # clinical_collection_name = lookup_disease('brain')
    # clinical_collection = db[clinical_collection_name]
    # clinical_data = clinical_collection.find()
    #
    # print(lookup_disease('brain'))
