"""PLSR Wrapper concrete implementation"""
import warnings
import os
import sys
import json

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
                scores = pca.fit_transform(self.mol_df)
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


def main():
    """Run the wrapper on an input file"""
    if len(sys.argv) > 1:
        json_filename = sys.argv[1]
    else:
        json_filename = "pca_input.json"
    with open(json_filename) as jsonfile:
        input_data = json.load(jsonfile)
    wrapper = PCAWrapper(**input_data)
    result = wrapper.run_algorithm()
    print(json.dumps(result, indent=4))


if __name__ == '__main__':
    main()
