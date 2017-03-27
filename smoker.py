"""return a (semi-)random input dataset"""
import random
import datetime
import sys
import pymongo
from bson.objectid import ObjectId

from timing import timeit
import do_plsr


db = do_plsr.db

def get_random_documents(collection, size, fields_wanted=None):
    pipeline = []
    sample = {"$sample": {"size": size}}
    pipeline.append(sample)
    projection = {}
    if fields_wanted:
        for field in fields_wanted:
            projection[field] = 1
    if projection:
        pipeline.append({"$project": projection})

    cursor = db[collection].aggregate(pipeline)
    ret = []
    for item in cursor:
        ret.append(item)
    return ret


def smoker(disease=None, mol_type=None, genes=None, samples=None,
           features=None, n_components=None):
    """
    Returns a (semi-)random dataset, for smoke testing.
    Supply all or none of the arguments, either as numbers
    or as a list of values.
    If you pass numbers, the function will return that many
    of the item. This only applies to genes samples, and features.
    n_components can only be 2 or 3.
    Not sure if the # of features has to be 2, or
    has to be > 1
    """
    collections = db.collection_names()

    samplemaps = [x for x in collections if x.endswith("_samplemap")]

    dashboards = [x for x in collections if x.endswith("_dashboard")]

    dash_diseases = [x.split("_")[0] for x in dashboards]

    diseases = [x.split("_")[0] for x in samplemaps]

    pruned_diseases = list(set(dash_diseases).intersection(set(diseases)))

    if not disease:
        disease = random.choice(pruned_diseases)
    lookup = db['lookup_oncoscape_datasources'].find_one({"disease":
                                                           disease})
    print("disease is: {}".format(disease))
    # get clinical collection by looking in
    # lookup_oncoscape_datasources.clinical.patient
    clinical_collection = lookup['clinical']['patient']
    # get mol_type by looking in
    # lookup_oncoscape_datasources.molecular (where disease=disease)
    # and picking a random 'type'
    if not mol_type:
        mol_type = random.choice(lookup['molecular'])['type']

    # get molecular collection by looking in
    # lookup_oncoscape_datasources.molecular where type is mol_type
    # and getting the 'collection' field
    molecular_collection = [y['collection'] \
        for y in lookup['molecular'] if y['type'] == mol_type][0]
    # those 2 steps could be done in one go?
    # get genes by looking in molecular collection and getting N random 'id's
    num_genes = None
    if genes is None:
        num_genes = random.randint(15,1000)
    elif isinstance(genes, int):
        num_genes = genes
    if num_genes: # otherwise genes is already a list of genes
        genes = get_random_documents(molecular_collection, num_genes, ['id'])
        genes = [x['id'] for x in genes]

    # get samples by looking in clinical_collection and getting N random 'id's
    # - need to map them from pt to sample names
    num_samples = None
    if samples is None:
        num_samples = random.randint(30, 1000)
    elif isinstance(samples, int):
        num_samples = samples
    if num_samples:
        samples = get_random_documents(clinical_collection, num_samples,
                                       ['patient_ID'])
        samples = [x['patient_ID'] for x in samples]
        mapper = db["{}_samplemap".format(disease)].find_one()
        reverse = {v: k for k, v in mapper.items()}
        tmp = []
        for x in samples:
            if not x in reverse:
                print("warning: {} does not occur in mapping table, dropping sample".format(x))
                continue
            tmp.append(reverse[x])
        samples = tmp

    # TODO does there have to be more than 1 feature?
    # TODO does there have to be only 2?
    # get features by looking in clinical collection, getting one record
    # and picking N random keys (excluding _id).
    # - does it have to be a key with a numeric value? or
    #   is that where factors come into play?
    # num_features = None
    # if features is None:
    possible_features = ['age_at_diagnosis',
                         'days_to_death',
                         'days_to_last_follow_up']
    num_features = None
    if features is None:
        num_features = 2#random.randint(1,3)
    elif isinstance(features, int):
        num_features = features
    if num_features:
        features = random.sample(set(possible_features), num_features)

    if n_components is None:
        n_components = random.randint(2,3)
    # return all of the above plus molecular & clinical collection names
    ret = dict(disease=disease,
               molecular_collection=molecular_collection,
               clinical_collection=clinical_collection,
               features=features, genes=genes, samples=samples,
               n_components=n_components)
    # fill in fields of ret...
    return ret

def summary(obj):
    sumstr = "disease: {}, features: {}, genes=({}), " + \
         "samples=({}), n_components={}"
    return sumstr.format(
          obj['disease'], obj['features'], len(obj['genes']),
          len(obj['samples']), obj['n_components'])

def success(obj):
    error = obj['reason'] if 'reason' in obj else "none"
    warning = obj['warning'] if 'warning' in obj else "none"
    return "errors: {}, warnings? {}".format(error, warning)



@timeit
def doit(obj):
    return do_plsr.plsr_wrapper(**obj)

def main():
    client = pymongo.MongoClient()
    localdb = client.smokes
    smokes = localdb.smokes
    if len(sys.argv) > 1:
        objid = sys.argv[1]
        outer = smokes.find_one({"_id": ObjectId(objid)})
        obj = outer['smoke']
        print("running saved instance from db.....")
        print(summary(obj))
        print("Running PLSR...")
        result = doit(obj)
        print(success(result))
        print()
        return

    for i in range(10):
        print("iteration {}:".format(i))
        obj = smoker()
        doc = dict(timestamp=datetime.datetime.now(), smoke=obj)
        obj_id = smokes.insert_one(doc).inserted_id

        print(summary(obj))
        print("Saved with ObjectID: {}".format(obj_id))
        print("Running PLSR...")
        result = doit(obj)
        print(success(result))
        print()

if __name__ == '__main__':
    main()
