"""Distance Wrapper concrete implementation"""
import warnings
import os
import sys
import json
import datetime

import numpy as np

from algorithm_wrapper import AbstractAlgorithmWrapper



class DistanceWrapper(AbstractAlgorithmWrapper):
    """Distance Wrapper concrete class"""

    @classmethod
    def get_input_parameters(cls):
        """Concrete implementation of abstract class method"""
        return sorted(['dataset1', 'molecular1','dataset2', 'molecular2',
                         'genes', 'samples', 'n_components'])

    @classmethod
    def get_algorithm_name(cls):
        """Concrete implementation of abstract method"""
        return "Distance"

    @classmethod
    def get_default_input_file(cls):
        """
        Return the name of a JSON
        file to be used as the default input file for example runs.
        """
        return "Distance_input.json"


   # constructor is in AbstractAlgorithmWrapper

    def run_algorithm(self):
        """Overriding abstract method"""

        # get molecular table 1 and 2
        # subset to relevant genes
        # calculate distance metric (correlation, euclidean, ...)
        

        old_showwarning = warnings.showwarning
        warnings.showwarning = self.custom_warn_function
        if self.error:
            print("There's an error, skipping Distance calculation...")
        else:
            try:
                then = datetime.datetime.now()
                print('"Distance calculation": {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))
                
                # subset the matrices to intersection & ordered genes across samples 
                
                D = np.corrcoef(self.mol_df, self.mol_df2)
                # sample to sample matrix of similarity metric
                
                diff = datetime.datetime.now() - then
                print(diff)
            except Exception as exc: # pylint: disable=broad-except
                self.error = str(exc)

        warnings.showwarning = old_showwarning

        if not self.error and np.all(np.isnan(D)): # no overlapping markers
            self.error = "results are NaN; no overlapping marker IDs?"

        ret_obj = {
                   "dataType": "Distance",
                   "D": None,
                   "metadata": None
                  }
        if self.error:
            ret_obj['reason'] = self.error
        else:
            ret2 = {"D": self.display_result(D.tolist(), self.mol_df)}
            ret_obj.update(ret2)
            if self.warning:
                ret_obj['warning'] = self.warning

        if os.getenv("WRAPPER_DEBUG"):
            import IPython
            IPython.embed()
        return ret_obj

if __name__ == '__main__':
    AbstractAlgorithmWrapper.entrypoint(DistanceWrapper)
