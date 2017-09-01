"""PLSR Wrapper concrete implementation"""
import warnings
import os
import sys
import json
import datetime

from sklearn.decomposition import PCA
import numpy as np

from algorithm_wrapper import AbstractAlgorithmWrapper



class PCAWrapper(AbstractAlgorithmWrapper):
    """PCA Wrapper concrete class"""

    @classmethod
    def get_input_parameters(cls):
        """Concrete implementation of abstract class method"""
        return sorted(['disease', 'genes', 'samples', 'molecular_collection',
                       'n_components'])

    @classmethod
    def get_algorithm_name(cls):
        """Concrete implementation of abstract method"""
        return "PCA"

    @classmethod
    def get_default_input_file(cls):
        """
        Return the name of a JSON
        file to be used as the default input file for example runs.
        """
        return "pca_input.json"


   # constructor is in AbstractAlgorithmWrapper

    def run_algorithm(self):
        """Overriding abstract method"""

        pca = PCA(n_components=self.n_components)

        old_showwarning = warnings.showwarning
        warnings.showwarning = self.custom_warn_function
        if self.error:
            print("There's an error, skipping pca.fit()...")
        else:
            try:
                then = datetime.datetime.now()
                print('fit_transform: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))
                scores = pca.fit_transform(self.mol_df)
                diff = datetime.datetime.now() - then
                print(diff)
            except Exception as exc: # pylint: disable=broad-except
                self.error = str(exc)

        warnings.showwarning = old_showwarning

        if not self.error and np.all(np.isnan(scores)): # all scores values are NaN
            self.error = "results are NaN; too few rows in input?"

        ret_obj = {"disease": self.disease,
                   "dataType": "PCA",
                   "score": "sample",
                   "loading": "hugo",
                   "default": False,
                   "scores": None,
                   "loadings": None,
                   "metadata": None
                  }
        if self.error:
            ret_obj['reason'] = self.error
        else:
            ret2 = {"scores": self.display_result(scores.tolist(), self.mol_df),
                    "loadings": self.display_result(pca.components_.transpose().tolist(),
                                                    self.mol_df, False),
                    "metadata": dict(variance=pca.explained_variance_ratio_.tolist())}
            ret_obj.update(ret2)
            if self.warning:
                ret_obj['warning'] = self.warning

        if os.getenv("WRAPPER_DEBUG"):
            import IPython
            IPython.embed()
        return ret_obj

if __name__ == '__main__':
    AbstractAlgorithmWrapper.entrypoint(PCAWrapper)
