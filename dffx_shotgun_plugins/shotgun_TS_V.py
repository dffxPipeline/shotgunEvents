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
    #reg.logger.debug('Loading logArgs plugin.')

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
        'Shotgun_Version_Change': ['sg_status_list']
    }
    reg.registerCallback(shotgunScriptName, shotgunScriptKey, shotgun_TS_V, matchEvents, None)

    # Set the logging level for this particular plugin. Let error and above
    # messages through but block info and lower. This is particularly usefull
    # for enabling and disabling debugging on a per plugin basis.
    reg.logger.setLevel(logging.INFO)

def shotgun_TS_V(sg, logger, event, args):
    """
    A callback that logs its arguments.

    @param sg: Shotgun instance.
    @param logger: A preconfigured Python logging.Logger object
    @param event: A Shotgun event.
    @param args: The args passed in at the registerCallback call.
    """
    if 'new_value' not in event['meta']:
        return

    else:
        versionTaskID = ''
        TaskStatusUpdate = ''
        versionID = ''
        lastVersionID = ''
        try:
            TaskStatusUpdate = event['meta']['new_value']
            ignoredStatusUpdates = ['vwd','wtg','na']
            if TaskStatusUpdate not in ignoredStatusUpdates:
                versionID = event['entity']['id']
                entityType = event['entity']['type']
                filters = [['id','is',versionID]]
                fields = ['sg_task']
                versionTaskID = sg_find(sg,'Version',filters,fields)['sg_task'].get('id')
                TaskStatusUpdateData = {'sg_status_list':TaskStatusUpdate}
                taskUpdate = sg.update ("Task",versionTaskID,TaskStatusUpdateData)

                logger.info("Task Status Updated To %s for Task ID %s Based on Version ID %s" % (str(TaskStatusUpdate),str(versionTaskID),str(versionID)))

            else:
                return
        except Exception as error:
            logger.info("Can't Update Task Status For %s Task ID: %s " % (str(versionTaskID),str(error)))
        try:
            versionSummary = []
            versionID = event['entity']['id']
            filters = [['id','is',versionID]]
            fields = ['entity','sg_task','project']
            versionDict = sg_entityDict=sg.find_one('Version',filters,fields)

            versionEntity = versionDict['entity']
            versionTask = versionDict['sg_task']
            versionProject = versionDict['project']

            versionSummary = sg.summarize( entity_type = 'Version', filters = [['entity', 'is', versionEntity],['sg_task', 'is', versionTask],['project', 'is', versionProject]],
                                            summary_fields=[{'field':'created_at','type':'latest'}],
                                            grouping=[{'field':'id','type':'exact','direction':'desc'}])['groups']

            if versionSummary != []:
                if len(versionSummary) >= 2:
                    latestVersionID = int(versionSummary[0]['group_name'])
                    lastVersionID = int(versionSummary[1]['group_name'])
                    lastVersionStatusFilters = [['id','is',lastVersionID]]
                    lastVersionStatusFields = ['sg_status_list']

                    if latestVersionID == versionID:
                        lastVersionStatus = sg_find(sg,'Task',lastVersionStatusFilters,lastVersionStatusFields)['sg_status_list']
                        if lastVersionStatus != 'apr':
                            # Version Name Based finding, for readability, but not the most exact (two versions can be named the same thing if user makes an error)
                            #         latestVersionID = sg.find('Version',filters = [['code', 'is', latestVersion],['project', 'is', versionProject]],fields = ['id'])[0]['id']
                            #         lastVersionID = sg.find('Version',filters = [['code', 'is', lastVersion],['project', 'is', versionProject]],fields = ['id'])[0]['id']
                            #         logger.info("%s" % (latestVersionID))
                            #         logger.info("%s" % (lastVersionID))
                            #
                            statusUpdate = 'vwd'
                            statusUpdateData = {'sg_status_list':str(statusUpdate)}
                            versionStatusUpdate = sg.update ("Version",lastVersionID,statusUpdateData)
                            logger.info("Version Status Updated To %s for Version ID %s Based on Version ID %s" % (str(statusUpdate),str(lastVersionID),str(latestVersionID)))

        except Exception as error:
            logger.info("Can't Update Status For %s Version ID: %s" % (str(lastVersionID),str(error)))
