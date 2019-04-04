import logging
import os
from datetime import datetime

from rascore import medicaid_model as sc
from rascore.scoring import (conditionHierarchy, directory)

logging.basicConfig(filename = os.path.join(directory, 'Logs\\Medicaid_Scoring.log'), level = logging.INFO, filemode = 'w')

def compute_risk_score(member):
    output ={
	        'memberKey':0,
	        'standardScores': {
		        'totalOpportunity': {
			        'score': 0.00,
			        'interceptValue': 0.00,
			        'demographicValue': 0.00,
			        'hierarchyValue': 0.00,
			        'diseaseInteractionValue': 0.00
		        },
		        'openOpportunity': {
			        'score': 0.00,
			        'hierarchyValue': 0.00,
			        'diseaseInteractionValue': 0.00
		        },
		        'confirmed': {
			        'score': 0.00,
			        'interceptValue': 0.00,
			        'demographicValue': 0.00,
			        'hierarchyValue': 0.00,
			        'diseaseInteractionValue': 0.00
		        }
	        },
	        'customScores': {
		        'OpenOpportunity': {
			        'score': 0.00,
			        'interceptValue': 0.00,
			        'demographicValue': 0.00,
			        'hierarchyValue': 0.00,
			        'diseaseInteractionValue': 0.00
		        }
	        },
             'successFlag':False,
             "reason":"Error:please check log file for more details"
        }
    #memberParams = sc.validateMemberParameters(dict(memberKey = '' if 'memberKey' not in member else member['memberKey'],
    #                                                gender = '' if 'gender' not in member else member['gender'],
    #                                                age = '' if 'age' not in member else member['age'],
    #                                                disabledFlag = '' if 'disabledFlag' not in member else member['disabledFlag'],
    #                                                lineOfBusiness = '' if 'lineOfBusiness' not in member else member['lineOfBusiness']))
    #memberId = memberParams['memberKey']
    for model in member['modelConditions']:
        modelParams = sc.validateModelParameters(dict(modelName = 'cdps' if 'name' not in model else model['name'], modelVersion = '' if 'version' not in model else model['version'], modelState = 'national' if 'state' not in model else model['state']))
        weightsRefData = sc.extractFileName('weights', modelParams['modelName'], modelParams['modelVersion'], modelParams['modelState'])
        crosswalkRefData = sc.extractFileName('map', modelParams['modelName'], modelParams['modelVersion'], modelParams['modelState'])
        hierarchyRefData = sc.extractFileName('hier', modelParams['modelName'], modelParams['modelVersion'], modelParams['modelState'])
        interactionRefData = sc.extractFileName('interaction', modelParams['modelName'], modelParams['modelVersion'], modelParams['modelState'])
        memberId=0
        try:
            memberParams = sc.validateMemberParameters(dict(memberKey = '' if 'memberKey' not in member else member['memberKey'],
                                                    gender = '' if 'gender' not in member else member['gender'],
                                                    age = '' if 'age' not in member else member['age'],
                                                    disabledFlag = '' if 'disabledFlag' not in member else member['disabledFlag'],
                                                    lineOfBusiness = '' if 'lineOfBusiness' not in member else member['lineOfBusiness']))
            memberId=memberParams['memberKey']
            modelKey = sc.generateModelKey(memberParams['age'], memberParams['disabledFlag'], model['type'].upper(),model['input'].upper(),memberId, modelWeight='ACUTE')
            refDataModelKey = modelKey.replace("_ACUTE", "")
            conditionsList = sc.applyConditionsRollupLogic(refDataModelKey, crosswalkRefData, model['conditions'], conditionHierarchy, memberId)
            hier_conditionsList = sc.applyAdditionalHierarchyRules(refDataModelKey, interactionRefData, conditionsList, memberId)
            hierarchyScoreTV = sc.getHierarchyScore(refDataModelKey, weightsRefData, hierarchyRefData, hier_conditionsList, memberId, conditionStatus = None)
            hierarchyScoreOV = sc.getHierarchyScore(refDataModelKey, weightsRefData, hierarchyRefData, hier_conditionsList, memberId, conditionStatus = 1)
            hierarchyScoreCV = sc.getHierarchyScore(refDataModelKey, weightsRefData, hierarchyRefData, hier_conditionsList, memberId, conditionStatus = 3)
            interactionConditionsList = sc.applyConditionsRollupLogic(refDataModelKey, crosswalkRefData, model['conditions'], conditionHierarchy, memberId)
            diScoreTV = sc.getDiseaseInteractionScore(refDataModelKey, weightsRefData, interactionRefData, interactionConditionsList, memberId, conditionStatus = None)
            diScoreOV = sc.getDiseaseInteractionScore(refDataModelKey, weightsRefData, interactionRefData, interactionConditionsList, memberId, conditionStatus = 1)
            diScoreCV = sc.getDiseaseInteractionScore(refDataModelKey, weightsRefData, interactionRefData, interactionConditionsList, memberId, conditionStatus = 3)
        except Exception:
            output['memberKey'] = '' if memberId ==0  else memberId
            return output
# if intercept or demographic gets failed

        try:
            interceptScore=sc.getInterceptScore(modelKey, weightsRefData, memberId)
        except:
            interceptScore = 0.00
            try:
                demographicScore = sc.getDemographicScore(modelKey, weightsRefData, memberParams['age'], memberParams['gender'], memberId)
            except:
                demographicScore=0.00
            priorityValue = getMemberScores(demographicScore, interceptScore, hierarchyScoreOV, diScoreOV,
                                            isIntercept=False, isDemographics=False)
            isIntercept = member['customScoreComponents']['interceptFlag']
            isDemographics = member['customScoreComponents']['demographicsFlag']
            customPriorityValue = getMemberScores(interceptScore, demographicScore, hierarchyScoreOV, diScoreOV,
                                                  isIntercept, isDemographics)
            return {
	        'memberKey': memberParams['memberKey'],
	        'standardScores': {
		        'totalOpportunity': {
			        'score': 0.00,
			        'interceptValue': 0.00,
			        'demographicValue': 0.00,
			        'hierarchyValue': 0.00,
			        'diseaseInteractionValue': 0.00
		        },
		        'openOpportunity': {
			        'score': priorityValue,
			        'hierarchyValue': hierarchyScoreOV,
			        'diseaseInteractionValue': diScoreOV
		        },
		        'confirmed': {
			        'score': 0.00,
			        'interceptValue': 0.00,
			        'demographicValue': 0.00,
			        'hierarchyValue': 0.00,
			        'diseaseInteractionValue': 0.00
		        }
	        },
	        'customScores': {
		        'OpenOpportunity': {
			        'score': customPriorityValue if (demographicScore!=0.00 and isDemographics==True and isIntercept!=True) else 0.000 ,
			        'interceptValue':interceptScore,
                        # interceptScore if isIntercept == True else 0.000,
			        'demographicValue': demographicScore if (demographicScore!=0.00 and isDemographics==True and isIntercept!=True) else 0.000,
			        'hierarchyValue': hierarchyScoreOV if (demographicScore!=0.00 and isDemographics==True and isIntercept!=True) else 0.000 ,
			        'diseaseInteractionValue': diScoreOV if (demographicScore!=0.00 and isDemographics==True and isIntercept!=True)   else 0.000
		        }
	        },
                'successFlag': False,
                'reason': "Error:please check log file for more details"

        }
    try:
        demographicScore = sc.getDemographicScore(modelKey, weightsRefData, memberParams['age'], memberParams['gender'],
                                                  memberId)
    except:
        demographicScore = 0.00
        priorityValue = getMemberScores(demographicScore, interceptScore, hierarchyScoreOV, diScoreOV,
                                        isIntercept=False, isDemographics=False)
        isIntercept = member['customScoreComponents']['interceptFlag']
        isDemographics = member['customScoreComponents']['demographicsFlag']
        customPriorityValue = getMemberScores(interceptScore, demographicScore, hierarchyScoreOV, diScoreOV,
                                              isIntercept, isDemographics)
        return {
            'memberKey': memberParams['memberKey'],
            'standardScores': {
                'totalOpportunity': {
                    'score': 0.00,
                    'interceptValue': 0.00,
                    'demographicValue': 0.00,
                    'hierarchyValue': 0.00,
                    'diseaseInteractionValue':0.00
                },
                'openOpportunity': {
                    'score': priorityValue,
                    'hierarchyValue': hierarchyScoreOV,
                    'diseaseInteractionValue': diScoreOV
                },
                'confirmed': {
                    'score': 0.00,
                    'interceptValue': 0.00,
                    'demographicValue': 0.00,
                    'hierarchyValue': 0.00,
                    'diseaseInteractionValue':0.00
                }
            },
            'customScores': {
                'OpenOpportunity': {
                    'score': customPriorityValue if(demographicScore == 0.00 and isDemographics != True and isIntercept==True) else 0.000,
                    'interceptValue': interceptScore if(demographicScore == 0.00 and isDemographics != True and isIntercept==True) else 0.000,
                    'demographicValue': 0.00,
                    'hierarchyValue': hierarchyScoreOV if(demographicScore == 0.00 and isDemographics != True and isIntercept==True) else 0.000,
                    'diseaseInteractionValue': diScoreOV if(demographicScore == 0.00 and isDemographics != True and isIntercept==True) else 0.000
                }
            },
            'successFlag': False,
            'reason': "Error:please check log file for more details"

        }
    totalOpportunityValue = getMemberScores(interceptScore, demographicScore, hierarchyScoreTV, diScoreTV,
                                           isIntercept=True, isDemographics=True)
    priorityValue = getMemberScores(interceptScore, demographicScore, hierarchyScoreOV, diScoreOV,
                                   isIntercept=False, isDemographics=False)
    confirmedValue = getMemberScores(interceptScore, demographicScore, hierarchyScoreCV, diScoreCV,
                                    isIntercept=True, isDemographics=True)
    isIntercept = member['customScoreComponents']['interceptFlag']
    isDemographics = member['customScoreComponents']['demographicsFlag']
    customPriorityValue = getMemberScores(interceptScore, demographicScore, hierarchyScoreOV, diScoreOV,
                                         isIntercept, isDemographics)

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
	        },
                'successFlag': True,
                'reason': "None"

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
    scores = round(interceptScorei + demographicScorei + hierarchyScore + diseaseInteractionScore, 3)
    return scores

#if __name__ == "__main__":
#    getRiskAdjustmentScore()

