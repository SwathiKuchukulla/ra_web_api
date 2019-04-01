from flask import Flask, flask, json, jsonify, redirect, request, url_for
from rascore import medicaid_engine
from werkzeug.utils import secure_filename

import jsonschema

app = Flask('apiserver')
app.config['JSON_SORT_KEYS'] = False


score_input_schema = {
    'type': 'object',
    'properties': {
        'memberKey': {'type': 'string'},
        'gender': {
            'enum': ['M', 'F']
        },
        'age': {'type': 'number'},
        'disabledFlag': {
            'type': 'boolean',
            'default': False
        },
        'lineOfBusiness': {'type': 'string'},
        'modelConditions': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'version': {'type': 'string'},
                    'state': {'type': 'string'},
                    'type': {'type': 'string'},
                    'input': {'type': 'string'},
                    'year': {'type': 'string'},
                    'conditions': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'code': {'type': 'string'},
                                'type': {'type': 'string'},
                                'version': {'type': 'string'},
                                'status': {'type': 'string'}
                            },
                            'required': ['code', 'type', 'version']
                        }
                    },
                },
                'required': ['name', 'version', 'type', 'input', 'year', 'conditions']
            }
        },
        'customScoreComponents': {
            'type': 'object',
            'properties': {
                'interceptFlag': {'type': 'boolean'},
                'demographicsFlag': {'type': 'boolean'}
            }
        }
    },
    'required': ['gender', 'age', 'modelConditions']
}


def new_error(code, message):
    return {'code': code, 'message': message}


@app.route('/score',  methods=['POST'])
def score():
    data = request.get_json()
    result = medicaid_engine.compute_risk_score(request.json)
    
    return json.dumps(result, sort_keys=False, indent=2)


# This example handles error raised by medicaid_engine.
# medicaid_engine raises TypeError if data is None
@app.route('/score_handle_engine_error',  methods=['POST'])
def score_handle_engine_error():
    data = request.get_json()

    try:
        result = medicaid_engine.compute_risk_score(request.json)
    except TypeError as e:
        error = new_error('INTERNAL_ERROR', str(e))
        return jsonify(error), 500

    return jsonify(result)


# This example use jsonschema to valida the input data
@app.route('/score_with_validation',  methods=['POST'])
def score_with_validation():
    data = request.get_json()

    try:
        jsonschema.validate(data, score_input_schema)
    except jsonschema.exceptions.ValidationError as e:
        error = new_error('INVALID_PARAMETER', e.message)
        return jsonify(error), 400

    result = medicaid_engine.compute_risk_score(request.json)
    return jsonify(result)


# This example uses json file as input data
@app.route('/score_with_file',  methods=['POST'])
def score_with_file():
    file = request.files['myfile']

    filename = secure_filename(file.filename) 
    file_save = file.save(os.path.join("C:\\Users\\srkuchukulla\\Source\\Repos\\ra_web_api\\", filename))
    with open(file_save) as f:
        file_content = f.read()

    return file_content

