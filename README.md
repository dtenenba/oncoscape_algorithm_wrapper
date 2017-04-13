# Algorithm Wrapper Microservice for Oncoscape

This is a web application that takes a JSON object as input, runs an
algorithm on the input, and returns JSON output.

Here are the currently supported algorithms, their endpoints, and example input
and output JSON.

Algorithm | Endpoint | Input Example | Output example
--- | --- | --- | ---
[PLSR](https://en.wikipedia.org/wiki/Partial_least_squares_regression) | `/plsr` | [sample_input2.json](sample_input2.json) | [sample_output2.json](sample_output2.json)
[PCA](https://en.wikipedia.org/wiki/Principal_component_analysis) | `/pca` | [pca_input.json](pca_input.json) | [pca_output.json](pca_output.json)


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

See the [comments](Dockerfile#L1)
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

Note that the Docker container used, `dtenenba/oncoscape_algorithm_wrapper`,
is rebuilt every time there is a push to
[this GitHub repository](.).
You can see build reports
[here](https://hub.docker.com/r/dtenenba/ooncoscape_algorithm_wrapper/builds/).

## Calling the service

The three methods above all start the service at
[http://localhost:8000/](http://localhost:8000/).

### `PLSR` example

This command will call the PLSR endpoint with some JSON input and display
the elapsed time used:

```bash
time curl -vX POST http://localhost:8000/plsr -d @sample_input2.json
```

### `PCA` example


This command will call the PCA endpoint with some JSON input and display
the elapsed time used:

```bash
time curl -vX POST http://localhost:8000/pca -d @pca_input.json
```

*Note*: You need to be in the same directory as this `README` in order for `curl` to find the
JSON input files used in these examples.



## Was my run successful?

If your run was NOT successful there will be a `reason` key
in the JSON output by the microservice, and the value of
that key will give some clue as to the error that occurred.
So clients should check to see if the `reason` key exists
before doing anything else.

You should also check the `warning` key. If it exists,
it will be a `list` of warnings produced by the PLSR
algorithm which may indicate a problem.


## Smoke Testing

`smoker.py` is a program that generates input to the algorithm wrapper
and then runs the wrapper with that input and tells you the result
(success or failure; warnings) and the time it took to run.

If no parameters are specified, the input generated is totally random,
but you can specify all aspects of the input, or just some of them.
You can also constrain it by saying how many genes you want in the input
(rather than specifying the actual genes).

This program requires a local instance of MongoDB (`mongod`) to be
running, because it saves the input objects it generates, in case you
want to re-run one of them for further debugging.

You need to specify the algorithm (currently `PCA` or `PLSR` with
the `-a` flag).
Run with no additional arguments
(e.g. `python smoker.py -a PLSR`), the script
will generate 10 random sets
of input data and call the PLSR wrapper 10 times with that data,
reporting the result and time it took to run.
For each input data set, you'll see something like this:

```
iteration 1:
disease is: paad
disease: paad, features: ['age_at_diagnosis', 'days_to_last_follow_up'], genes=(19), samples=(185), n_components=3
Saved with ObjectID: 58d96d580f45e77ae6c25738
Running PLSR...
'doit' ('', {}) 0.40 sec
errors: none, warnings? none
```

This tells us a bit about the input data set that was generated (disease,
features, number of genes and samples, and dimensions (n_components)).
Also in this case, PLSR ran without errors or warnings in 0.4 seconds.

The generated input data sets are stored in a MongoDB database called `smokes`
in a collection also called `smokes`. If you want to re-run the last
data set, its ObjectID should be on the screen, but if you don't see it,
just find the ObjectID of the document with the most recent
timestamp (by pasting the following into RoboMongo or a `mongo smokes` shell ):

```javascript
db.getCollection('smokes').find({}, {_id: 1}).sort({"timestamp": -1}).limit(1).next()
```



Then add that ID to the script command to run just that data set, for example:

    python smoker.py -i 58d96d580f45e77ae6c25738



## Remaining Work

* Add unit tests
* Add continuous integration
* More error handling


## Problems?

Please file [an issue](../../issues/).
