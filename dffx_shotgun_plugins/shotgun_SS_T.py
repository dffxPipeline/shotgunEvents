"""
For detailed information please see

http://shotgunsoftware.github.com/shotgunEvents/api.html

## shotgun_logArgs: Logs all events that occur and generates a logfile in the specified directory found in the shotgun_logging.conf file ##
"""

rootSoftwareDir = ['Z:\\Server\\Tools','S:\\',]
dffxModulesExists = ''
configFilePathExists = ''

import os

def getPath(paths):
    for path in paths:
        if os.path.exists(path):
            return path

__version__ = '0.9'
__version_info__ = (0, 9)

for dir in rootSoftwareDir:
    path_to_dffxModules=[os.path.join(dir,'modules\\shotgun')]
    path_to_dffxModules = getPath(path_to_dffxModules)
    if path_to_dffxModules != None:
        dffxModulesExists = path_to_dffxModules

import sys
if dffxModulesExists != '':
    sys.path.insert(1,dffxModulesExists)
    import dffx_configParser
import logging

def sg_find(connection,entityType,userFilters,userFields):
    sg_entityDict=connection.find_one(entityType,userFilters,userFields)
    return sg_entityDict

def all_same(items):
    return all(x == items[0] for x in items)

def changeStatus(sg,shotID,status):
    status_out = ''
    shotStatusUpdateData = {'sg_status_list':str(status)}
    taskUpdate = sg.update ( "Shot",shotID,shotStatusUpdateData )
    if status == 'hld':
        status_out = 'Shot On Hold'
    if status == 'rev':
        status_out = 'Pending Review'
    if status == 'mn':
        status_out = 'Mod Needed'
    if status == 'pcr':
        status_out = 'Pending Client Review'
    if status =='if':
        status_out = 'Shot Marked Internal Final'
    if status =='fin':
        status_out = 'Shot Marked Final'
    if status == 'omt':
        status_out = 'Shot Omitted'
    if status == 'ip':
        status_out = 'Shot Marked In Progress'
    if status == 'rnd':
        status_out = 'Shot is Rendering'
    return ( "Shot ID %s: Status Updated to %s" % ( str(shotID),str(status_out) ) )

def parseConfig():

    for dir in rootSoftwareDir:
        path_to_config=[os.path.join(dir,'configs\\shotgun')]
        configFilePath = getPath(path_to_config)
        if configFilePath != None:
            configFilePathExists = configFilePath

    if configFilePathExists != '':
        configFileName = 'shotgun_TD.conf'
        configPath = dffx_configParser._getConfigPath(configFilePathExists,configFileName)
        configObj = dffx_configParser.Config(configPath)
        shotgunScriptName = configObj.getScriptName()
        shotgunScriptKey = configObj.getScriptKey()

        configInfo = [shotgunScriptName,shotgunScriptKey]

        return configInfo
    else:
        raise Exception ('Config path not found, searched %s' % ', '.join(paths))

def registerCallbacks(reg):
    """Register all necessary or appropriate callbacks for this plugin."""

    # Specify who should recieve email notifications when they are sent out.
    #
    #reg.setEmails('me@mydomain.com')

    # Use a preconfigured logging.Logger object to report info to log file or
    # email. By default error and critical messages will be reported via email
    # and logged to file, all other levels are logged to file.
    #

    # Register a callback to into the event processing system.
    #
    # Arguments:
    # - Shotgun script name
    # - Shotgun script key
    # - Callable
    # - Argument to pass through to the callable
    # - A filter to match events to so the callable is only invoked when
    #   appropriate
    #
    reg.logger.debug('Loading shotgun_SS_T plugin.')

    configInfo = parseConfig()
    shotgunScriptName = configInfo[0]
    shotgunScriptKey = configInfo[1]

    matchEvents = {
        'Shotgun_Task_Change': ['sg_status_list']
    }
    reg.registerCallback(shotgunScriptName, shotgunScriptKey, shotgun_SS_T, matchEvents, None)

    # Set the logging level for this particular plugin. Let error and above
    # messages through but block info and lower. This is particularly usefull
    # for enabling and disabling debugging on a per plugin basis.
    reg.logger.setLevel(logging.INFO)

def shotgun_SS_T(sg, logger, event, args):
    """
    A callback that logs its arguments.

    @param sg: Shotgun instance.
    @param logger: A preconfigured Python logging.Logger object
    @param event: A Shotgun event.
    @param args: The args passed in at the registerCallback call.
    """
    currentTaskStatus = ''
    shotTaskStatusList=[]

    try:
        if 'new_value' not in event['meta']:
            return

        else:
            currentTaskID = event['entity']['id']
            logger.info("%s" % str(currentTaskID))
            currentTaskFilters = [['id','is',currentTaskID]]
            logger.info("%s" % str(currentTaskFilters))

            currentTaskFields = ['sg_status_list']
            logger.info("%s" % str(currentTaskFilters))
            currentTaskStatus = sg_find(sg,'Task',currentTaskFilters,currentTaskFields)['sg_status_list']
            logger.info("%s" % str(currentTaskStatus))
            shotStatusUpdateData,revCount,modCount,ipCount,pcrCount,hldCount,internalFinalCount,disregardCount = ( '' for i in range(8) )
            filters=[['id','is',currentTaskID]]
            fields=['entity']
            try:
                shotID=sg_find(sg,'Task',filters,fields)['entity']['id']
                shotFilter = [['id','is',shotID]]
                shotFields = ['tasks']
                shotTasks = sg_find(sg,'Shot',shotFilter,shotFields)['tasks']

                for task in shotTasks:
                    shotTaskID = task.get('id')
                    taskFilters = [['id','is',shotTaskID]]
                    taskFields = ['sg_status_list']
                    taskStatus = sg_find(sg,'Task',taskFilters,taskFields)['sg_status_list']
                    shotTaskStatusList.append(taskStatus)

                ipStatusList = ['ip', 'rdy', 'wtg', 'lgt', 'lgtCmp']

                disregardCount = shotTaskStatusList.count('omt') + shotTaskStatusList.count('na')
                internalFinalCount = shotTaskStatusList.count('if') + shotTaskStatusList.count('fin') + shotTaskStatusList.count('CBB') + disregardCount
                hldCount = shotTaskStatusList.count('hld') + internalFinalCount
                pcrCount = shotTaskStatusList.count('pcr') + hldCount
                ipCount =  shotTaskStatusList.count('ip') + shotTaskStatusList.count('wtg') + shotTaskStatusList.count('rdy') + shotTaskStatusList.count('lgtcmp') + shotTaskStatusList.count('lgt') + pcrCount
                rndCount = shotTaskStatusList.count('rnd') + ipCount
                modCount = shotTaskStatusList.count('mn') + rndCount
                revCount = shotTaskStatusList.count('rev') + modCount

                logger.info("%s" % str(shotTaskStatusList))

                if 'rev' == currentTaskStatus:
                    if revCount == len(shotTaskStatusList):
                        statusInfo = changeStatus(sg,shotID,'rev')
                        logger.info("%s" % str(statusInfo))

                elif 'mn' == currentTaskStatus:
                    if modCount == len(shotTaskStatusList):
                        statusInfo = changeStatus(sg,shotID,'mn')
                        logger.info("%s" % str(statusInfo))
                    elif 'rev' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'rev')
                        logger.info("%s" % str(statusInfo))

                elif 'rnd' == currentTaskStatus:
                    if rndCount == len(shotTaskStatusList):
                        statusInfo = changeStatus(sg,shotID,'rnd')
                        logger.info("%s" % str(statusInfo))
                    elif 'rev' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'rev')
                        logger.info("%s" % str(statusInfo))
                    elif 'mn' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'mn')
                        logger.info("%s" % str(statusInfo))

                elif currentTaskStatus in ipStatusList:
                    if ipCount == len(shotTaskStatusList):
                        statusInfo = changeStatus(sg,shotID,'ip')
                        logger.info("%s" % str(statusInfo))
                    elif 'rev' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'rev')
                        logger.info("%s" % str(statusInfo))
                    elif 'mn' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'mn')
                        logger.info("%s" % str(statusInfo))
                    elif 'rnd' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'rnd')
                        logger.info("%s" % str(statusInfo))

                elif 'pcr' == currentTaskStatus:
                    if pcrCount == len(shotTaskStatusList):
                        statusInfo = changeStatus(sg,shotID,'pcr')
                        logger.info("%s" % str(statusInfo))
                    elif 'rev' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'rev')
                        logger.info("%s" % str(statusInfo))
                    elif 'mn' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'mn')
                        logger.info("%s" % str(statusInfo))
                    elif 'rnd' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'rnd')
                        logger.info("%s" % str(statusInfo))
                    elif bool( set(ipStatusList) & set(shotTaskStatusList) ):
                        statusInfo = changeStatus(sg,shotID,'ip')
                        logger.info("%s" % str(statusInfo))

                elif 'hld' == currentTaskStatus:
                    if hldCount == len(shotTaskStatusList):
                        statusInfo = changeStatus(sg,shotID,'hld')
                        logger.info("%s" % str(statusInfo))
                    elif 'rev' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'rev')
                        logger.info("%s" % str(statusInfo))
                    elif 'mn' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'mn')
                        logger.info("%s" % str(statusInfo))
                    elif 'rnd' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'rnd')
                        logger.info("%s" % str(statusInfo))
                    elif bool( set(ipStatusList) & set(shotTaskStatusList) ):
                        statusInfo = changeStatus(sg,shotID,'ip')
                        logger.info("%s" % str(statusInfo))
                    elif 'pcr' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'pcr')
                        logger.info("%s" % str(statusInfo))

                elif 'if' == currentTaskStatus:
                    if internalFinalCount == len(shotTaskStatusList):
                        statusInfo = changeStatus(sg,shotID,'if')
                        logger.info("%s" % str(statusInfo))
                    elif 'hld' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'hld')
                        logger.info("%s" % str(statusInfo))
                    elif 'rev' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'rev')
                        logger.info("%s" % str(statusInfo))
                    elif 'mn' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'mn')
                        logger.info("%s" % str(statusInfo))
                    elif 'rnd' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'rnd')
                        logger.info("%s" % str(statusInfo))
                    elif bool( set(ipStatusList) & set(shotTaskStatusList) ):
                        statusInfo = changeStatus(sg,shotID,'ip')
                        logger.info("%s" % str(statusInfo))
                    elif 'pcr' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'pcr')
                        logger.info("%s" % str(statusInfo))

                elif 'fin' in currentTaskStatus:
                    if all_same( shotTaskStatusList ) == True:
                        statusInfo = changeStatus(sg,shotID,'fin')
                        logger.info("%s" % str(statusInfo))
                    elif 'hld' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'hld')
                        logger.info("%s" % str(statusInfo))
                    elif 'rev' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'rev')
                        logger.info("%s" % str(statusInfo))
                    elif 'mn' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'mn')
                        logger.info("%s" % str(statusInfo))
                    elif 'rnd' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'rnd')
                        logger.info("%s" % str(statusInfo))
                    elif bool( set(ipStatusList) & set(shotTaskStatusList) ):
                        statusInfo = changeStatus(sg,shotID,'ip')
                        logger.info("%s" % str(statusInfo))
                    elif 'pcr' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'pcr')
                        logger.info("%s" % str(statusInfo))
                    elif 'if' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'if')
                        logger.info("%s" % str(statusInfo))

                elif 'omt' == currentTaskStatus:
                    if all_same( shotTaskStatusList ) == True:
                        statusInfo = changeStatus(sg,shotID,'omt')
                        logger.info("%s" % str(statusInfo))
                    elif 'hld' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'hld')
                        logger.info("%s" % str(statusInfo))
                    elif 'rev' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'rev')
                        logger.info("%s" % str(statusInfo))
                    elif 'mn' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'mn')
                        logger.info("%s" % str(statusInfo))
                    elif 'rnd' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'rnd')
                        logger.info("%s" % str(statusInfo))
                    elif bool( set(ipStatusList) & set(shotTaskStatusList) ):
                        statusInfo = changeStatus(sg,shotID,'ip')
                        logger.info("%s" % str(statusInfo))
                    elif 'pcr' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'pcr')
                        logger.info("%s" % str(statusInfo))
                    elif 'if' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'if')
                        logger.info("%s" % str(statusInfo))
                    elif 'fin' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'fin')
                        logger.info("%s" % str(statusInfo))

                elif 'wtg' == currentTaskStatus:
                    if all_same( shotTaskStatusList ) == True:
                        statusInfo = changeStatus(sg,shotID,'omt')
                        logger.info("%s" % str(statusInfo))
                    elif 'hld' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'hld')
                        logger.info("%s" % str(statusInfo))
                    elif 'rev' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'rev')
                        logger.info("%s" % str(statusInfo))
                    elif 'mn' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'mn')
                        logger.info("%s" % str(statusInfo))
                    elif 'rnd' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'rnd')
                        logger.info("%s" % str(statusInfo))
                    elif bool( set(ipStatusList) & set(shotTaskStatusList) ):
                        statusInfo = changeStatus(sg,shotID,'ip')
                        logger.info("%s" % str(statusInfo))
                    elif 'pcr' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'pcr')
                        logger.info("%s" % str(statusInfo))
                    elif 'if' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'if')
                        logger.info("%s" % str(statusInfo))
                    elif 'fin' in shotTaskStatusList:
                        statusInfo = changeStatus(sg,shotID,'fin')
                        logger.info("%s" % str(statusInfo))

                else:
                    logger.info( "Shot ID %s: Status Not Updated" % ( str(shotID) ) )
            except Exception as error:
                logger.info("%s" % ( str(error) ) )
    except Exception as error:
        logger.info("%s" % ( str(error) ) )
