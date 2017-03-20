FROM ubuntu:16.04

RUN apt-get update -y

# python3-dev is needed to install pymongo from source
# and thereby get the C extensions, for faster performance.


RUN apt-get install -y python3 python3-dev python3-pip git

RUN git clone https://github.com/dtenenba/oncoscape_plsr.git

RUN cd oncoscape_plsr

RUN pip3 install -r requirements.txt

EXPOSE 8000

COMMAND ["./run.sh"]
