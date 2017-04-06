"""PLSR Wrapper concrete implementation"""
import warnings
import os
import sys
import json

from sklearn.cross_decomposition import PLSRegression
import numpy as np

from algorithm_wrapper import AbstractAlgorithmWrapper



class PLSRWrapper(AbstractAlgorithmWrapper):
    """PLSR Wrapper concrete class"""

    @classmethod
    def get_input_parameters(cls):
        return sorted(['disease', 'genes', 'samples', 'features',
                       'molecular_collection', 'clinical_collection',
                       'n_components'])

   # constructor is in AbstractAlgorithmWrapper

    def run_algorithm(self):
        """Overriding abstract method"""
        pls2 = PLSRegression(n_components=self.n_components)

        old_showwarning = warnings.showwarning
        warnings.showwarning = self.custom_warn_function
        if self.error:
            print("There's an error, skipping pls2.fit()...")
        else:
            try:
                pls2.fit(self.mol_df, self.clin_df)
            except Exception as exc: # pylint: disable=broad-except
                self.error = str(exc)

        warnings.showwarning = old_showwarning

        if not self.error and np.all(np.isnan(pls2.x_scores_)): # all x_scores_ values are NaN
            self.error = "results are NaN; too few rows in input?"

        ret_obj = {"disease": self.disease,
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
        if self.error:
            ret_obj['reason'] = self.error
        else:
            ret2 = {"x_scores": self.display_result(pls2.x_scores_.tolist(), self.mol_df),
                    "y_scores": self.display_result(pls2.y_scores_.tolist(), self.clin_df),
                    "x.loadings": self.display_result(pls2.x_loadings_.tolist(), self.mol_df,
                                                      False),
                    "y.loadings": self.display_result(pls2.y_loadings_.tolist(), self.clin_df,
                                                      False),
                    "metadata": self.display_result(pls2.coef_.tolist(), self.mol_df, False)}
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
        json_filename = "sample_input2.json"
    with open(json_filename) as jsonfile:
        input_data = json.load(jsonfile)
    wrapper = PLSRWrapper(**input_data)
    result = wrapper.run_algorithm()
    print(json.dumps(result, indent=4))


if __name__ == '__main__':
    main()
