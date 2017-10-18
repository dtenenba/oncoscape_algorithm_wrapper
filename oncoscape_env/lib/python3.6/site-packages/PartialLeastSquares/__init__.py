#!/usr/bin/env python


import sys

if sys.version_info[0] == 3:
    from PartialLeastSquares.PartialLeastSquares import __version__
    from PartialLeastSquares.PartialLeastSquares import __author__
    from PartialLeastSquares.PartialLeastSquares import __date__
    from PartialLeastSquares.PartialLeastSquares import __url__
    from PartialLeastSquares.PartialLeastSquares import __copyright__
    from PartialLeastSquares.PartialLeastSquares import PartialLeastSquares
else:
    from PartialLeastSquares import __version__
    from PartialLeastSquares import __author__
    from PartialLeastSquares import __date__
    from PartialLeastSquares import __url__
    from PartialLeastSquares import __copyright__
    from PartialLeastSquares import PartialLeastSquares

