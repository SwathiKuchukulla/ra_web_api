REST API Examples 
=================

This branch contains REST API examples.


## Installing

```sh
pip install git+https://github.com/SwathiKuchukulla/ra_web_api.git

```

## Starting server

You can start the REST API server using [Flask CLI](http://flask.pocoo.org/docs/1.0/cli/#command-line-interface)

```sh
# For linux and mac:
$ FLASK_APP=apiserver.app FLASK_ENV=development flask run

# For Windows cmd:
set FLASK_APP=apiserver.app
set FLASK_ENV=development
flask run
```

And you will see output similar to this

```sh
 * Serving Flask app "apiserver.app" (lazy loading)
 * Environment: development
 * Debug mode: on
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 360-877-902
```

## Endpoints

- POST /score
- POST /score_handle_engine_error
- POST /score_with_validation
- POST /score_with_file
