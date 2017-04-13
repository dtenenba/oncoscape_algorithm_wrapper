"""
Contains an abstract parent class for algorithm wrappers.
"""
from abc import ABCMeta, abstractmethod
import os
import sys
import json

import pymongo
import pandas as pd


class AbstractAlgorithmWrapper(object): # pylint: disable=too-many-instance-attributes
    """A an abstract parent class for algorithms (PLSR, PCA, etc.)"""
    __metaclass__ = ABCMeta

    def init_db(self):
        """Initialize MongoDB connection"""
        # TODO - add connection pooling
        self.mongo_url = os.getenv("MONGO_URL")
        if not self.mongo_url:
            print("MONGO_URL is not defined in environment.")
            print("See the file setup_env.sh.example for more information.")
            print("Exiting.")
            sys.exit(1)
        self.client = pymongo.MongoClient(self.mongo_url)
        self.db = self.client.tcga # pylint: disable=invalid-name

    def __init__(self, disease, genes, samples, # pylint: disable=too-many-arguments
                 molecular_collection, n_components,
                 clinical_collection=None,
                 features=None):
        """Constructor. Inheriting classes do not need to define __init__"""
        self.init_db()

        self.disease, self.genes, self.samples, self.molecular_collection, \
          self.n_components, self.clinical_collection, self.features = \
          disease, genes, samples, molecular_collection, n_components, \
          clinical_collection, features

        self.mol_df = self.get_data_frame(self.molecular_collection,
                                          {"id": {"$in": genes}})

        if self.samples: # subset by samples
            subset = [x for x in self.mol_df.index if x in self.samples]
            self.mol_df = self.mol_df.loc[subset]
        self.mol_df.sort_index(inplace=True)

        if self.clinical_collection:
            self.clin_df = self.clin_coll_to_df(self.clinical_collection,
                                                self.disease,
                                                self.features,
                                                self.samples)

            # subset clin_df by rows of mol_df
            subset = list(self.mol_df.index)
            self.clin_df = self.clin_df.loc[subset]

            # does clin_df have any NAs in it? If so, remove those rows:
            clin_rows_to_drop =  \
              self.clin_df[self.clin_df.isnull().any(axis=1)].index.tolist()
            self.clin_df.dropna(inplace=True) # just drop them in one go from clin_df

        # same for mol_df
        mol_rows_to_drop = \
          self.mol_df[self.mol_df.isnull().any(axis=1)].index.tolist()
        self.mol_df.dropna(inplace=True)

        if self.clinical_collection:
            # Now we need to make sure that the rows we dropped above are dropped
            # from the corresponding data frame as well.

            # NOTE - this way of dropping rows could remove valid rows
            # if there is more than one row with the same name as a result
            # of mapping from pt to sample names.

            # from clin_df:
            #  drop all rows from mol_rows_to_drop that are in clin_df.index
            self.clin_df.drop(list(set(self.clin_df.index).intersection(set(mol_rows_to_drop))),
                              inplace=True)

            # from mol_df:
            # drop all rows from clin_rows_to_drop that are in mol_df.index
            self.mol_df.drop(list(set(self.mol_df.index).intersection(set(clin_rows_to_drop))),
                             inplace=True)

        self.error = None
        self.warning = []

        # make sure that we still have rows in the data frames!
        if not len(self.mol_df.index):
            self.error = "No non-NA rows in molecular input"
        if self.clinical_collection and not len(self.clin_df.index):
            self.error = "No non-NA rows in clinical input"


    def custom_warn_function(self, message, *args): # pylint: disable=unused-argument
        """Catch warnings thrown by algorithm"""
        self.warning.append(str(message))
        print("We got a warning! {}".format(message))

    @classmethod
    @abstractmethod
    def get_input_parameters(cls):
        """Subclasses override this to indicate input parameters."""
        pass

    @classmethod
    @abstractmethod
    def get_algorithm_name(cls):
        """Subclasses override this to return algorithm name"""
        pass

    @classmethod
    @abstractmethod
    def get_default_input_file(cls):
        """
        Subclasses override this to return the name of a JSON
        file to be used as the default input file for example runs.
        """
        pass


    @classmethod
    def entrypoint(cls, algorithm):
        """Run the wrapper on an input file"""
        if len(sys.argv) > 1:
            json_filename = sys.argv[1]
        else:
            json_filename = algorithm.get_default_input_file()
        with open(json_filename) as jsonfile:
            input_data = json.load(jsonfile)
        wrapper = algorithm(**input_data)
        result = wrapper.run_algorithm()
        print(json.dumps(result, indent=4))


    @abstractmethod
    def run_algorithm(self):
        """
        Inheriting classes must implement this.
        It should return a JSON-serializable object to return
        to the client.
        """
        pass

    def cursor_to_data_frame(self, cursor): # pylint: disable=no-self-use
        """Iterate through a Mongo cursor & put result in pandas DataFrame"""
        dfr = pd.DataFrame()
        for item in cursor:
            key = item['id']
            dfr[key] = pd.Series(list(item['data'].values()),
                                 index=list(item['data'].keys()))
        return dfr


    def get_data_frame(self, collection, query=None, projection=None):
        """Return a data frame given a mongo collection, query, & projection"""
        if not query:
            query = {}
        if not projection:
            projection = {}
        cursor = self.db[collection].find(query, None)
        dfr = self.cursor_to_data_frame(cursor)
        dfr.sort_index(inplace=True)
        return dfr


    def get_projection(self, items): # pylint: disable=no-self-use
        """Given a list, make a hash suitable for a mongo projection"""
        if not items:
            return None
        ret = {}
        for item in items:
            ret[item] = 1
        return ret

    def display_result(self, inputdata, data_frame, row_wise=True): # pylint: disable=no-self-use
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


    def clin_coll_to_df(self, clinical_collection, disease, # pylint: disable=too-many-locals
                        features, samples):
        """Convert clinical collection to a pandas DataFrame"""
        mapcol = "{}_samplemap".format(disease)
        sample_pt_map = self.db[mapcol].find_one()
        if samples:
            wanted_pts = [sample_pt_map[x] for x in samples]
            query = {"patient_ID": {"$in": wanted_pts}}
        else:
            query = {}

        projection = self.get_projection(features + ["patient_ID"])
        cursor = self.db[clinical_collection].find(query, projection)
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
