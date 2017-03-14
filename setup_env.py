#!/usr/bin/env python
"""
Run me like this:

    eval $(./setup_py)

That will set the MONGO_URL environment variable which you
can then use with the mongo command-line client:

    mongo $MONGO_URL

"""

import config

print("export MONGO_URL='{}'".format(config.MONGO_URL))
