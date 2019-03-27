import json
import os
import datetime
import re
import logging

from typing import List
from collections import defaultdict
from rascore.scoring import referenceFilesData

def validateMemberParameters(memberParams):
    cleanMemberParams = memberParams.copy()
    if cleanMemberParams['memberKey'] == '':
        logging.error('Error - MemberId: not found; Scoring can not be computed')
    if cleanMemberParams['gender'] == '':
        logging.info('MemberId: %s; Error - Gender not found; Effects Demographic Component', cleanMemberParams['memberKey'])
    elif cleanMemberParams['gender'] not in ('f', 'm', 'F', 'M'):
        logging.info('MemberId: %s; Error - Gender not valid; Effects Demographic Component', cleanMemberParams['memberKey'])
    else: 
        cleanMemberParams['gender'] = cleanMemberParams['gender'].lower()
    if cleanMemberParams['age'] == '':
        logging.info('MemberId: %s; Error - Age not found; Effects Demographic, Hierarchy & Disease Interaction Components', cleanMemberParams['memberKey'])
    elif cleanMemberParams['age'] != int(cleanMemberParams['age']):
        logging.info('MemberId: %s; Error - Age not valid; Effects Demographic, Hierarchy & Disease Interaction Components', cleanMemberParams['memberKey'])        
    if cleanMemberParams['disabledFlag'] == '':
        cleanMemberParams['disabledFlag'] = False
    if cleanMemberParams['lineOfBusiness'] == '':
        logging.info('MemberId: %s; Error - Line Of Business not found; Effects Intercept, Demographic, Hierarchy & Disease Interaction Components', cleanMemberParams['memberKey'])
    elif cleanMemberParams['lineOfBusiness'].upper() not in ('MEDICARE', 'MEDICAID', 'NEXT GEN', 'ACA'):
        logging.info('MemberId: %s; Error - Line Of Business not valid; Effects Intercept, Demographic, Hierarchy & Disease Interaction Components', cleanMemberParams['memberKey'])
    else: 
        cleanMemberParams['lineOfBusiness'] = cleanMemberParams['lineOfBusiness'] 
    return cleanMemberParams


def validateModelParameters(modelParams):
    cleanModelParams = modelParams.copy()
    cleanModelParams['modelName'] = 'cdps' if cleanModelParams['modelName'] == '' else cleanModelParams['modelName'].lower()
    cleanModelParams['modelState'] = 'national' if cleanModelParams['modelState'] == '' else cleanModelParams['modelState'].lower()
    if cleanModelParams['modelVersion'] == '':
        logging.info('Error - Model Version not found; Effects Intercept, Demographic, Hierarchy & Disease Interaction Components')
    else:
        cleanModelParams['modelVersion'] = ('v' + cleanModelParams['modelVersion'].replace(".","")).lower()      
    return cleanModelParams


def generateModelKey(age, disabledFlag, modelType, modelInput, modelWeight = 'ACUTE'):
    """ what about use case for DADC - aid category """
    if disabledFlag == False:
        aidValue = 'AC' if age < 18 else 'AA'
    elif disabledFlag == True:
        aidValue = 'DC' if age < 18 else 'DA'
    if modelType == 'CONCURRENT':
       modelTypeValue = 'CON' 
    elif modelType == 'PROSPECTIVE':
         modelTypeValue = 'PRO'
    modelInputValue = 'DX_RX' if modelInput == 'DX+RX' else modelInput
    modelKey = aidValue + '_' + modelTypeValue + '_' + modelInputValue + '_' + modelWeight
    return modelKey


def getInterceptScore(modelKey, weightsRefData, memberId):
    """ """
    modelWeights = referenceFilesData[weightsRefData]
    InterceptScore = 0.00
    try:
        InterceptScore = modelWeights['Intercept'][modelKey]
    except KeyError as e:
        logging.error("MemberId: %s; Error occured while generating Intercept Score for %s", memberId, modelKey)           
    return round(InterceptScore, 3)


def getDemographicScore(modelKey, weightsRefData, age, gender, memberId):
    """ """
    modelWeights = referenceFilesData[weightsRefData] 
    demographicScore = 0.00
    for key in modelWeights:
        if key.startswith('a_') or (key.endswith('f') or key.endswith('m')): 
            split = (key.split('_'))                                        
            lowBound = int(split[1])                                        
            highBoundWithGender = split[2]                                  
            highBound = int(highBoundWithGender[:-1])                       
            genderKey = highBoundWithGender[-1:]
            if age >= lowBound and age <= highBound and gender == genderKey:
                try:
                    demographicScore = modelWeights[key][modelKey]
                    break
                except KeyError as e:
                    logging.error("MemberId: %s; Error occured while generating Demographic Score for %s for %s", memberId, modelKey, key)
                    continue
    return round(demographicScore, 3)


def applyConditionsRollupLogic(modelKey, crosswalkRefData, diagnosisList, conditionHierarchy, memberId):
    """ Roll Up Logic
        add try and Catch blocks
        Dx invalid - Need to update reason in Output file ?
            1. invalid version
            2. Dx Not found in crosswalk file """
    modelCrosswalk = referenceFilesData[crosswalkRefData]
    condHierMaxRank = 1     # Take default as Open in Condition Hiererchy
    conditions = defaultdict(lambda: condHierMaxRank)

    for diagnosis in diagnosisList:      
        code = diagnosis['code']
        status = diagnosis['status']
        try:
            condition = modelCrosswalk[modelKey][code]
            for each_condition in condition:
                prevRank = conditions[each_condition]
                rank = conditionHierarchy[status]
                conditions.update({each_condition: conditionHierarchy[status]})
                conditions[each_condition] = max(prevRank, rank)
        except KeyError as e:
            logging.error("MemberId: %s; Conditions Rollup Logic: %s & %s not found in model Crosswalk", memberId, modelKey, code)
            continue
    return conditions


def applyAdditionalHierarchyRules(modelKey, interactionRefData, conditions, memberId):
    """ #"0": Add   "1": Replace"""
    modelInteraction = referenceFilesData[interactionRefData]
    interactionConditions = conditions.copy()
    for condition in conditions:
        try:
            if condition in modelInteraction[modelKey]['1']:
                newCondition = modelInteraction[modelKey]['1'][condition][0]
                interactionConditions[newCondition] = interactionConditions.pop(condition)    
        except:
            logging.info("MemberId: %s; Apply Additional Hierarchy Rules: condition [%s]  gets replaced by newCondition", memberId, condition)
            pass 
    return interactionConditions


def getHierarchyScore(modelKey, weightsRefData, hierarchyRefData, conditionsList, memberId, conditionStatus = None):
    """ conditionStatus = 0: consider all status (RTOV)"""
    #{'AIDSH': 2, 'SKCVL': 2, 'CNSM': 2, 'PSYML': 3, 'SKCL': 2, 'SKCM': 2, 'METH': 3}
    modelWeights = referenceFilesData[weightsRefData]
    modelHierarchy = referenceFilesData[hierarchyRefData]
    if conditionStatus is None:             
        initialCondtions = list(conditionsList.keys())
    else: 
        initialCondtions = [condition for condition, status in conditionsList.items() if conditionStatus == status]    

    hierarchyConditions = []
    condition_set = set(initialCondtions)
    HierarchyScore = 0.0
    try:    
        for hierarchy in modelHierarchy[modelKey]:
            for condition in hierarchy:
                if condition in condition_set:
                    hierarchyConditions.append(condition)
                    break 
        weightsRefKey = modelKey + '_ACUTE'
        for condition in hierarchyConditions:
            if condition in modelWeights and weightsRefKey in modelWeights[condition]:
                HierarchyScore = HierarchyScore + modelWeights[condition][weightsRefKey]
    except KeyError as e:
        logging.error("MemberId: %s; Error occured while generating Hierarchy Score for %s", memberId, modelKey)
    return round(HierarchyScore, 3)


def getDiseaseInteractionScore(modelKey, weightsRefData, interactionRefData, conditionsList, memberId, conditionStatus = None):
    """ #"0": Add   "1": Replace"""
    modelWeights = referenceFilesData[weightsRefData]
    modelInteraction = referenceFilesData[interactionRefData]
    if conditionStatus is None:             
        initialCondtions = list(conditionsList.keys())
    else: 
        initialCondtions = [condition for condition, status in conditionsList.items() if conditionStatus == status]
    
    finalConditions = []
    for condition in initialCondtions:
        try:
            if condition in modelInteraction[modelKey]['0']:
                interactionConditions = modelInteraction[modelKey]['0'][condition]
                for iCondition in interactionConditions:
                    finalConditions.append(iCondition) 
        except:
            logging.info("MemberId: %s; Applying Interaction Rules: condition [%s]  gets replaced by newCondition(s)", memberId, condition)
            pass

    diseaseInteractionScore = 0.0
    weightsRefKey = modelKey + '_ACUTE'
    for condition in finalConditions:
        try:
            if condition in modelWeights and weightsRefKey in modelWeights[condition]:
                    diseaseInteractionScore = diseaseInteractionScore + modelWeights[condition][weightsRefKey]
        except KeyError as e:
            logging.error("MemberId: %s; Error occured while generating Disease Interaction Score for %s", memberId, modelKey)
    return round(diseaseInteractionScore, 3)


def extractFileName(fileType, modelName, modelVersion, modelState):
    """model parameter gets changed to LOB -- Also, reference file naming convention should be changed"""
    fileName = '{}_{}_{}'.format(modelName, modelVersion, fileType) if modelState == 'national' else '{}_{}_{}_{}'.format(modelName, modelVersion, modelState, fileType)
    return fileName


def loadFileContent(filePath):
    """Directory path can be defined in Input file """
    with open(os.path.join(filePath), 'r') as fp:
        fileContent = json.load(fp)
    return fileContent


def generateOutputfile(filePath, fileContent):
    """Directory path can be defined in Input file """
    with open(os.path.join(filePath), 'w') as fp:
        json.dump(fileContent, fp, indent = 2)

