# PLSR Microservice for Oncoscape

This is a web application which takes a JSON object as input
([example here](https://github.com/dtenenba/oncoscape_plsr/blob/master/sample_input2.json))
and produces a JSON output file
([example here](https://github.com/dtenenba/oncoscape_plsr/blob/master/sample_output2.json)) containing the result of a
[PLSR](https://en.wikipedia.org/wiki/Partial_least_squares_regression) calculation.

This application requires Python 3.

## Running the Microservice

Typically this application accesses the `dev` instance of
Oncoscape's MongoDB database, so it must be run inside
the Hutch network.


### Setup

The application requires that the `MONGO_URL` environment variable be
set. We provide a tool to set it easily:

```bash
cp setup_env.sh.example setup_env.sh
# edit setup_env.sh to contain the actual Mongo URL
```

Now you can set MONGO_URL with the following command:

```bash
. setup_env.sh
```

There are three ways to run the microservice:

### 1) Run via Flask

This is what you'll typically use when you are developing
the code.

First, create and activate a
[Python virtual environment](https://python-docs.readthedocs.io/en/latest/dev/virtualenvs.html).
The use of [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/)
is recommended.
If you have Python 2 and 3 on your system, you need to specify which
version is used when you create your virtual environment. Here's
how to do that with `virtualenvwrapper`:

```bash
mkvirtualenv --python $(which python3) plsr_env
```

Install all dependencies:

```bash
pip install -r requirements.txt
```

You can now run the Flask application with this command:

```bash
FLASK_APP=flask_app.py FLASK_DEBUG=1 flask run -p 8000
```

### 2) Run via gunicorn

[Gunicorn](http://gunicorn.org/) is a faster and more robust server.

Assuming you have created a virtual environment and installed dependencies
as described in the previous step, all you have to do to run
under gunicorn is:

```bash
./run.sh
```

This will spawn four worker processes. The number of processes
can be made configurable via an environment variable in the future.

### 3) Run via Docker

Make sure MONGO_URL is set in your environment as above, and
Docker is installed.

See the [comments](https://github.com/dtenenba/oncoscape_plsr/blob/master/Dockerfile#L1)
at the top of the `Dockerfile` for important information about
how to configure your Docker daemon.

Then run:

```bash
./run_container.sh
```

If you want to develop inside the container, run

```bash
./test_container.sh
```

instead. This will mount the current directory inside the container
and drop you at a bash prompt in that directory.

Note that the Docker container used, `dtenenba/oncoscape_plsr`,
is rebuilt every time there is a push to
[this GitHub repository](https://github.com/dtenenba/oncoscape_plsr).
You can see build reports
[here](https://hub.docker.com/r/dtenenba/oncoscape_plsr/builds/).

## Calling the service

The three methods above all start the service at
[http://localhost:8000](http://localhost:8000).

This command will call the service with some JSON input and display
the elapsed time used:

```bash
time curl -vX POST http://localhost:8000 -d @sample_input2.json
```

## Remaining Work

* Add unit tests
* Add continuous integration
* More error handling


## Problems?

Please file [an issue](https://github.com/dtenenba/oncoscape_plsr/issues).
