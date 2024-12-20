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
    reg.logger.debug('Loading shotgun_TS_V plugin.')

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
    if event:
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
                    #logger.info("TaskStatusUpdateData %s\n" % (TaskStatusUpdateData))
                    taskUpdate = sg.update ("Task",versionTaskID,TaskStatusUpdateData)
                    logger.info("Task Status Updated To %s for Task ID %s Based on Version ID %s" % (str(TaskStatusUpdate),str(versionTaskID),str(versionID)))
            except Exception as error:
                logger.info("Can't Update Task Status For %s Task ID: %s " % (str(versionTaskID),str(error)))
            try:
                if versionTaskID:
                    task_filters = [['id','is',versionTaskID]]
                    task_fields = ['sg_parent_task', 'step', 'entity']
                    sg_parent_task_dict = sg_find(sg,'Task',task_filters,task_fields)
                    if sg_parent_task_dict:
                        #logger.info("sg_parent_task %s\n" % (sg_parent_task_dict))
                        task_dict = sg_parent_task_dict.get("sg_parent_task", None)
                        #logger.info("task_dict %s\n" % (task_dict))
                        sg_parent_task_id = task_dict.get("id", None)
                        #logger.info("sg_parent_task_id %s\n" % (sg_parent_task_id))
                        sg_parent_task_name = task_dict.get("name", None)
                        #logger.info("sg_parent_task_name %s\n" % (sg_parent_task_name))
                        step_dict = sg_parent_task_dict.get("step", None)
                        logger.info("step_dict %s\n" % (step_dict))
                        entity_dict = sg_parent_task_dict.get("entity", None)
                        logger.info("entity_dict %s\n" % (entity_dict))
                        if step_dict and entity_dict:
                            step_name = step_dict.get("name", None)
                            step_task_filters = [['entity','is',entity_dict], ['content','is',step_name]]
                            step_task_fields = ['content', 'id', 'entity']
                            sg_step_task_dict = sg_find(sg,'Task',step_task_filters,step_task_fields)
                            logger.info("sg_step_task_dict %s\n" % (sg_step_task_dict))
                            if sg_step_task_dict:
                                step_task_name = sg_step_task_dict.get("content", None)
                                if sg_parent_task_name and step_task_name:
                                    step_task_id = sg_step_task_dict.get("id", None)
                                    if step_task_name != sg_parent_task_name:
                                        step_task_update = sg.update ("Task",step_task_id,TaskStatusUpdateData)

                        if sg_parent_task_id:
                            sg_parent_task_update = {'sg_status_list': 'omt'}
                            parent_task_update = sg.update ("Task",sg_parent_task_id,sg_parent_task_update)
                            logger.info("Updated sg_parent_task %s, id: %s, to Omitted\n" % (sg_parent_task_name, sg_parent_task_id))
            except Exception as error:
                logger.info("Can't Update Task Status For %s ERROR: %s\n" % (str(versionTaskID),str(error)))
            try:
                versionSummary = []
                versionID = event['entity']['id']
                filters = [['id','is',versionID]]
                fields = ['entity','sg_task','project']
                versionDict = sg.find_one('Version', filters, fields)
                versionEntity = versionDict['entity']
                versionTask = versionDict['sg_task']
                versionProject = versionDict['project']
                #logger.info(str(versionEntity))
                #logger.info(str(versionTask))
                #logger.info(str(versionProject))
                if versionEntity != None and versionTask != None and versionProject != None:
                    versionSummary = sg.summarize( entity_type = 'Version', filters = [['entity', 'is', versionEntity],['sg_task', 'is', versionTask],['project', 'is', versionProject]],
                                                    summary_fields=[{'field':'created_at','type':'latest'}],
                                                    grouping=[{'field':'id','type':'exact','direction':'desc'}])['groups']
                    if versionSummary != []:
                        if len(versionSummary) >= 2:
                            latestVersionID = int(versionSummary[0]['group_name'])
                            lastVersionID = int(versionSummary[1]['group_name'])
                            lastVersionStatusFilters = [['id', 'is', lastVersionID]]
                            lastVersionStatusFields = ['sg_status_list']

                            # logger.info(str(versionSummary))
                            # logger.info(str(latestVersionID))
                            # logger.info(str(lastVersionID))

                            if latestVersionID == versionID:
                                lastVersionStatus_dict = sg_find(sg,'Version', lastVersionStatusFilters, lastVersionStatusFields)
                                if 'sg_status_list' in lastVersionStatus_dict.keys():
                                    lastVersionStatus = lastVersionStatus_dict['sg_status_list']
                                    #logger.info(str(lastVersionStatus))
                                    if lastVersionStatus != 'apr' and lastVersionStatus != None:
                                        statusUpdate = 'vwd'
                                        statusUpdateData = {'sg_status_list':str(statusUpdate)}
                                        versionStatusUpdate = sg.update ("Version", lastVersionID, statusUpdateData)
                                        logger.info("Version Status Updated To %s for Version ID %s Based on Version ID %s" % (str(statusUpdate), str(lastVersionID), str(latestVersionID)))

            except Exception as error:
                logger.info("Can't Update Status For %s Version ID: %s" % (str(lastVersionID), str(error)))
