#!/bin/bash


# This will run the container, mount the current directory
# inside it as /plsr, and put you at a bash prompt in that directory.
# You can make changes in your favorite
# editor and have them reflected immediately inside the container.

docker run -ti --rm -p 8000:8000 \
  -e "MONGO_URL=$MONGO_URL" \
  --name oncoscape_plsr -v $(pwd):/plsr -w \
  /plsr dtenenba/oncoscape_plsr bash
