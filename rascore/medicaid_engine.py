import logging
import os
from datetime import datetime

from rascore import medicaid_model as sc
from rascore.scoring import (conditionHierarchy, directory)

#logging.basicConfig(filename = os.path.join(directory, 'Logs\\Medicaid_Scoring.log'), level = logging.INFO, filemode = 'w')

def compute_risk_score(member):
    memberParams = sc.validateMemberParameters(dict(memberKey = '' if 'memberKey' not in member else member['memberKey'], 
                                                    gender = '' if 'gender' not in member else member['gender'], 
                                                    age = '' if 'age' not in member else member['age'], 
                                                    disabledFlag = '' if 'disabledFlag' not in member else member['disabledFlag'], 
                                                    lineOfBusiness = '' if 'lineOfBusiness' not in member else member['lineOfBusiness']))
    memberId = memberParams['memberKey']
    for model in member['modelConditions']:
        modelKey = sc.generateModelKey(memberParams['age'], memberParams['disabledFlag'], model['type'].upper(), model['input'].upper(), modelWeight = 'ACUTE')
        refDataModelKey = modelKey.replace("_ACUTE","")
        modelParams = sc.validateModelParameters(dict(modelName = 'cdps' if 'name' not in model else model['name'], modelVersion = '' if 'version' not in model else model['version'], modelState = 'national' if 'state' not in model else model['state']))
        
        weightsRefData = sc.extractFileName('weights', modelParams['modelName'], modelParams['modelVersion'], modelParams['modelState'])
        crosswalkRefData = sc.extractFileName('map', modelParams['modelName'], modelParams['modelVersion'], modelParams['modelState'])
        hierarchyRefData = sc.extractFileName('hier', modelParams['modelName'], modelParams['modelVersion'], modelParams['modelState'])
        interactionRefData = sc.extractFileName('interaction', modelParams['modelName'], modelParams['modelVersion'], modelParams['modelState'])
    
        interceptScore = sc.getInterceptScore(modelKey, weightsRefData, memberId)
        demographicScore = sc.getDemographicScore(modelKey, weightsRefData, memberParams['age'], memberParams['gender'], memberId)
    
        conditionsList = sc.applyConditionsRollupLogic(refDataModelKey, crosswalkRefData, model['conditions'], conditionHierarchy, memberId)
        hier_conditionsList = sc.applyAdditionalHierarchyRules(refDataModelKey, interactionRefData, conditionsList, memberId)
        hierarchyScoreTV = sc.getHierarchyScore(refDataModelKey, weightsRefData, hierarchyRefData, hier_conditionsList, memberId, conditionStatus = None)
        hierarchyScoreOV = sc.getHierarchyScore(refDataModelKey, weightsRefData, hierarchyRefData, hier_conditionsList, memberId, conditionStatus = 1)
        hierarchyScoreCV = sc.getHierarchyScore(refDataModelKey, weightsRefData, hierarchyRefData, hier_conditionsList, memberId, conditionStatus = 3)
        
        interactionConditionsList = sc.applyConditionsRollupLogic(refDataModelKey, crosswalkRefData, model['conditions'], conditionHierarchy, memberId)   
        diScoreTV = sc.getDiseaseInteractionScore(refDataModelKey, weightsRefData, interactionRefData, interactionConditionsList, memberId, conditionStatus = None)
        diScoreOV = sc.getDiseaseInteractionScore(refDataModelKey, weightsRefData, interactionRefData, interactionConditionsList, memberId, conditionStatus = 1)
        diScoreCV = sc.getDiseaseInteractionScore(refDataModelKey, weightsRefData, interactionRefData, interactionConditionsList, memberId, conditionStatus = 3)
    
    totalOpportunityValue = getMemberScores(interceptScore, demographicScore, hierarchyScoreTV, diScoreTV, isIntercept = True, isDemographics = True)
    priorityValue = getMemberScores(interceptScore, demographicScore, hierarchyScoreOV, diScoreOV, isIntercept = False, isDemographics = False)
    confirmedValue = getMemberScores(interceptScore, demographicScore, hierarchyScoreCV, diScoreCV, isIntercept = True, isDemographics = True)    
    isIntercept = member['customScoreComponents']['interceptFlag']
    isDemographics = member['customScoreComponents']['demographicsFlag']
    customPriorityValue = getMemberScores(interceptScore, demographicScore, hierarchyScoreOV, diScoreOV, isIntercept, isDemographics)    
    return {
	        'memberKey': memberParams['memberKey'],
	        'standardScores': {
		        'totalOpportunity': {
			        'score': totalOpportunityValue,
			        'interceptValue': interceptScore,
			        'demographicValue': demographicScore,
			        'hierarchyValue': hierarchyScoreTV,
			        'diseaseInteractionValue': diScoreTV
		        },
		        'openOpportunity': {
			        'score': priorityValue,
			        'hierarchyValue': hierarchyScoreOV,
			        'diseaseInteractionValue': diScoreOV
		        },
		        'confirmed': {
			        'score': confirmedValue,
			        'interceptValue': interceptScore,
			        'demographicValue': demographicScore,
			        'hierarchyValue': hierarchyScoreCV,
			        'diseaseInteractionValue': diScoreCV
		        }
	        },
	        'customScores': {
		        'OpenOpportunity': {
			        'score': customPriorityValue,
			        'interceptValue': interceptScore if isIntercept == True else 0.000,
			        'demographicValue': demographicScore if isDemographics == True else 0.000,
			        'hierarchyValue': hierarchyScoreOV,
			        'diseaseInteractionValue': diScoreOV
		        }
	        }
        }

def getRiskAdjustmentScore(inputFilePath, outputFilePath):
    startTime = datetime.now()
    inputFile = sc.loadFileContent(inputFilePath)  
    output = []
    for member in inputFile:
        memberScore = compute_risk_score(member)
        output.append(memberScore)
    sc.generateOutputfile(outputFilePath, output)
    endTime = datetime.now()
    logging.info('Duration: {}'.format(endTime - startTime))
    return output

def getMemberScores(interceptScore, demographicScore, hierarchyScore, diseaseInteractionScore, isIntercept = False, isDemographics = False):
    interceptScorei = interceptScore if isIntercept == True else 0.000
    demographicScorei = demographicScore if isDemographics == True else 0.000
    scores = interceptScorei + demographicScorei + hierarchyScore + diseaseInteractionScore
    return scores

#if __name__ == "__main__":
#    getRiskAdjustmentScore()

