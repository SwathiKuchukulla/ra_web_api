"""
    This is supporting file for Risk Scoring Calculator
"""
import os
import sys
import json
import math
import re
import collections

from datetime import datetime
from decimal import *
from pprint import pprint
from collections import defaultdict

conditionHierarchy = {
	"Open": 1,
	"Confirmed-PCP": 2,
	"Confirmed-Claim": 3
}

directory = "C:\\Users\\srkuchukulla\\Source\\Repos\\risk-adjustment-scoring\\risk-scoring-ui\\risk-scoring-ui\\risk_scoring_ui\\"
#directory = ""

def defineInputOutputFilePaths(inputFilePath, outputFilePath):
    """defining Input & Output FilePaths """
    with open(inputFilePath) as fp:
        data_input = json.load(fp)
        print(type(data_input))
        data_input['RA Score'] = 0
    with open(outputFilePath, 'w') as outputFile:
        json.dump(data_input, outputFile)
    with open(outputFilePath) as file:
        data = json.load(file)
    return data

def load_ref_data():                #Implement Lazy loading 
    modelData = defaultdict(dict)
    current_path = os.path.dirname(__file__)
    fileDirectory = os.path.join(current_path, 'ReferenceFiles', 'Medicaid')
    for fileName in os.listdir(fileDirectory):
        with open(os.path.join(fileDirectory, fileName), 'r') as fp:
            modelData[fileName.replace('.json', '')] = json.load(fp)    
    return modelData

referenceFilesData = load_ref_data()
