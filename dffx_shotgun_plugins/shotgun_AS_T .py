"""
For detailed information please see

http://shotgunsoftware.github.com/shotgunEvents/api.html

## shotgun_logArgs: Logs all events that occur and generates a logfile in the specified directory found in the shotgun_logging.conf file ##
"""

rootSoftwareDir = [r'\\intrepid\Server\Tools']
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

def changeStatus(sg,assetID,status):
    status_out = ''
    if status:
        shotStatusUpdateData = {'sg_status_list':str(status)}
        if shotStatusUpdateData:
            taskUpdate = sg.update ( "Asset", assetID, shotStatusUpdateData )
        if status == 'hld':
            status_out = 'Asset On Hold'
        if status == 'rev':
            status_out = 'Pending Review'
        if status == 'mn':
            status_out = 'Mod Needed'
        if status == 'pcr':
            status_out = 'Pending Client Review'
        if status =='if':
            status_out = 'Asset Marked Internal Final'
        if status =='fin':
            status_out = 'Asset Marked Final'
        if status == 'omt':
            status_out = 'Asset Omitted'
        if status == 'ip':
            status_out = 'Asset Marked In Progress'
        if status == 'rnd':
            status_out = 'Asset is Rendering'
        if status == '4k':
            status_out = 'Asset is Pending Quality Check'
        if status == 'fdi':
            status_out = 'Asset is Pending DI'
        if status == 'fdd':
            status_out = 'Asset is Pending Director/Studio Approval'
        if status == 'tfn':
            status_out = 'Asset Needs Tech Fix'
        return ( "Asset ID %s: Status Updated to %s" % ( str(assetID),str(status_out) ) )

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
    # - Assetgun script name
    # - Assetgun script key
    # - Callable
    # - Argument to pass through to the callable
    # - A filter to match events to so the callable is only invoked when
    #   appropriate
    #
    reg.logger.debug('Loading shotgun_AS_T plugin.')

    configInfo = parseConfig()
    shotgunScriptName = configInfo[0]
    shotgunScriptKey = configInfo[1]

    matchEvents = {
        'Shotgun_Task_Change': ['sg_status_list']
    }
    reg.registerCallback(shotgunScriptName, shotgunScriptKey, shotgun_AS_T, matchEvents, None)

    # Set the logging level for this particular plugin. Let error and above
    # messages through but block info and lower. This is particularly usefull
    # for enabling and disabling debugging on a per plugin basis.
    reg.logger.setLevel(logging.INFO)

def shotgun_AS_T(sg, logger, event, args):
    """
    A callback that logs its arguments.

    @param sg: Assetgun instance.
    @param logger: A preconfigured Python logging.Logger object
    @param event: A Assetgun event.
    @param args: The args passed in at the registerCallback call.
    """
    currentTaskStatus = ''
    assetTaskStatusList=[]

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
                assetID=sg_find(sg,'Task',filters,fields)['entity']['id']
                assetFilter = [['id','is',assetID]]
                assetFields = ['tasks']
                assetTasks = sg_find(sg,'Asset',assetFilter,assetFields)['tasks']

                for task in assetTasks:
                    assetTaskID = task.get('id')
                    taskFilters = [['id','is',assetTaskID]]
                    taskFields = ['sg_status_list']
                    taskStatus = sg_find(sg,'Task',taskFilters,taskFields)['sg_status_list']
                    assetTaskStatusList.append(taskStatus)

                ipStatusList = ['ip', 'rdy', 'wtg', 'lgt', 'lgtCmp']

                disregardCount = assetTaskStatusList.count('omt') + assetTaskStatusList.count('na')
                internalFinalCount = assetTaskStatusList.count('if') + assetTaskStatusList.count('fin') + assetTaskStatusList.count('CBB') + disregardCount
                hldCount = assetTaskStatusList.count('hld') + internalFinalCount
                pcrCount = assetTaskStatusList.count('pcr') + hldCount
                ipCount =  assetTaskStatusList.count('ip') + assetTaskStatusList.count('wtg') + assetTaskStatusList.count('rdy') + assetTaskStatusList.count('lgtcmp') + assetTaskStatusList.count('lgt') + pcrCount
                rndCount = assetTaskStatusList.count('rnd') + ipCount
                modCount = assetTaskStatusList.count('mn') + rndCount
                revCount = assetTaskStatusList.count('rev') + modCount

                #logger.info("%s" % str(assetTaskStatusList))

                if 'rev' == currentTaskStatus:
                    if revCount == len(assetTaskStatusList):
                        statusInfo = changeStatus(sg,assetID,'rev')
                        logger.info("%s" % str(statusInfo))

                elif 'mn' == currentTaskStatus:
                    if modCount == len(assetTaskStatusList):
                        statusInfo = changeStatus(sg,assetID,'mn')
                        logger.info("%s" % str(statusInfo))
                    elif 'rev' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'rev')
                        logger.info("%s" % str(statusInfo))

                elif 'rnd' == currentTaskStatus:
                    if rndCount == len(assetTaskStatusList):
                        statusInfo = changeStatus(sg,assetID,'rnd')
                        logger.info("%s" % str(statusInfo))
                    elif 'rev' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'rev')
                        logger.info("%s" % str(statusInfo))
                    elif 'mn' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'mn')
                        logger.info("%s" % str(statusInfo))

                elif '4k' == currentTaskStatus:
                    statusInfo = changeStatus(sg, assetID, '4k')
                    logger.info("%s" % str(statusInfo))

                elif 'fdi' == currentTaskStatus:
                    statusInfo = changeStatus(sg, assetID, 'fdi')
                    logger.info("%s" % str(statusInfo))

                elif 'fdd' == currentTaskStatus:
                    statusInfo = changeStatus(sg, assetID, 'fdd')
                    logger.info("%s" % str(statusInfo))

                elif 'tfn' == currentTaskStatus:
                    statusInfo = changeStatus(sg, assetID, 'tfn')
                    logger.info("%s" % str(statusInfo))

                elif currentTaskStatus in ipStatusList:
                    if ipCount == len(assetTaskStatusList):
                        statusInfo = changeStatus(sg,assetID,'ip')
                        logger.info("%s" % str(statusInfo))
                    elif 'rev' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'rev')
                        logger.info("%s" % str(statusInfo))
                    elif 'mn' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'mn')
                        logger.info("%s" % str(statusInfo))
                    elif 'rnd' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'rnd')
                        logger.info("%s" % str(statusInfo))

                elif 'pcr' == currentTaskStatus:
                    if pcrCount == len(assetTaskStatusList):
                        statusInfo = changeStatus(sg,assetID,'pcr')
                        logger.info("%s" % str(statusInfo))
                    elif 'rev' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'rev')
                        logger.info("%s" % str(statusInfo))
                    elif 'mn' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'mn')
                        logger.info("%s" % str(statusInfo))
                    elif 'rnd' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'rnd')
                        logger.info("%s" % str(statusInfo))
                    elif bool( set(ipStatusList) & set(assetTaskStatusList) ):
                        statusInfo = changeStatus(sg,assetID,'ip')
                        logger.info("%s" % str(statusInfo))

                elif 'hld' == currentTaskStatus:
                    if hldCount == len(assetTaskStatusList):
                        statusInfo = changeStatus(sg,assetID,'hld')
                        logger.info("%s" % str(statusInfo))
                    elif 'rev' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'rev')
                        logger.info("%s" % str(statusInfo))
                    elif 'mn' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'mn')
                        logger.info("%s" % str(statusInfo))
                    elif 'rnd' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'rnd')
                        logger.info("%s" % str(statusInfo))
                    elif bool( set(ipStatusList) & set(assetTaskStatusList) ):
                        statusInfo = changeStatus(sg,assetID,'ip')
                        logger.info("%s" % str(statusInfo))
                    elif 'pcr' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'pcr')
                        logger.info("%s" % str(statusInfo))

                elif 'if' == currentTaskStatus:
                    if internalFinalCount == len(assetTaskStatusList):
                        statusInfo = changeStatus(sg,assetID,'if')
                        logger.info("%s" % str(statusInfo))
                    elif 'hld' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'hld')
                        logger.info("%s" % str(statusInfo))
                    elif 'rev' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'rev')
                        logger.info("%s" % str(statusInfo))
                    elif 'mn' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'mn')
                        logger.info("%s" % str(statusInfo))
                    elif 'rnd' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'rnd')
                        logger.info("%s" % str(statusInfo))
                    elif bool( set(ipStatusList) & set(assetTaskStatusList) ):
                        statusInfo = changeStatus(sg,assetID,'ip')
                        logger.info("%s" % str(statusInfo))
                    elif 'pcr' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'pcr')
                        logger.info("%s" % str(statusInfo))

                elif 'fin' in currentTaskStatus:
                    if all_same( assetTaskStatusList ) == True:
                        statusInfo = changeStatus(sg,assetID,'fin')
                        logger.info("%s" % str(statusInfo))
                    elif 'hld' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'hld')
                        logger.info("%s" % str(statusInfo))
                    elif 'rev' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'rev')
                        logger.info("%s" % str(statusInfo))
                    elif 'mn' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'mn')
                        logger.info("%s" % str(statusInfo))
                    elif 'rnd' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'rnd')
                        logger.info("%s" % str(statusInfo))
                    elif bool( set(ipStatusList) & set(assetTaskStatusList) ):
                        statusInfo = changeStatus(sg,assetID,'ip')
                        logger.info("%s" % str(statusInfo))
                    elif 'pcr' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'pcr')
                        logger.info("%s" % str(statusInfo))
                    elif 'if' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'if')
                        logger.info("%s" % str(statusInfo))
                    elif 'omt' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'fin')
                        logger.info("%s" % str(statusInfo))

                elif 'omt' == currentTaskStatus:
                    if all_same( assetTaskStatusList ) == True:
                        statusInfo = changeStatus(sg,assetID,'omt')
                        logger.info("%s" % str(statusInfo))
                    elif 'hld' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'hld')
                        logger.info("%s" % str(statusInfo))
                    elif 'rev' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'rev')
                        logger.info("%s" % str(statusInfo))
                    elif 'mn' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'mn')
                        logger.info("%s" % str(statusInfo))
                    elif 'rnd' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'rnd')
                        logger.info("%s" % str(statusInfo))
                    elif bool( set(ipStatusList) & set(assetTaskStatusList) ):
                        statusInfo = changeStatus(sg,assetID,'ip')
                        logger.info("%s" % str(statusInfo))
                    elif 'pcr' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'pcr')
                        logger.info("%s" % str(statusInfo))
                    elif 'if' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'if')
                        logger.info("%s" % str(statusInfo))
                    elif 'fin' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'fin')
                        logger.info("%s" % str(statusInfo))

                elif 'wtg' == currentTaskStatus:
                    if all_same( assetTaskStatusList ) == True:
                        statusInfo = changeStatus(sg,assetID,'omt')
                        logger.info("%s" % str(statusInfo))
                    elif 'hld' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'hld')
                        logger.info("%s" % str(statusInfo))
                    elif 'rev' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'rev')
                        logger.info("%s" % str(statusInfo))
                    elif 'mn' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'mn')
                        logger.info("%s" % str(statusInfo))
                    elif 'rnd' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'rnd')
                        logger.info("%s" % str(statusInfo))
                    elif bool( set(ipStatusList) & set(assetTaskStatusList) ):
                        statusInfo = changeStatus(sg,assetID,'ip')
                        logger.info("%s" % str(statusInfo))
                    elif 'pcr' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'pcr')
                        logger.info("%s" % str(statusInfo))
                    elif 'if' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'if')
                        logger.info("%s" % str(statusInfo))
                    elif 'fin' in assetTaskStatusList:
                        statusInfo = changeStatus(sg,assetID,'fin')
                        logger.info("%s" % str(statusInfo))
                else:
                    logger.info( "Asset ID %s: Status Not Updated" % ( str(assetID) ) )
            except Exception as error:
                logger.info("%s" % ( str(error) ) )
    except Exception as error:
        logger.info("%s" % ( str(error) ) )
