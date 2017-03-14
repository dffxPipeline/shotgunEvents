"""
For detailed information please see

http://shotgunsoftware.github.com/shotgunEvents/api.html

## shotgun_logArgs: Logs all events that occur and generates a logfile in the specified directory found in the shotgun_logging.conf file ##
"""

rootSoftwareDir = ['Z:\\Server\\Tools','S:\\']
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
    reg.logger.debug('Loading shotgun_TS_DSD plugin.')
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

    configInfo = parseConfig()
    shotgunScriptName = configInfo[0]
    shotgunScriptKey = configInfo[1]

    matchEvents = {
        'Shotgun_Task_Change': ['sg_status_list']
    }

    reg.registerCallback(shotgunScriptName, shotgunScriptKey, shotgun_TS_DSD, matchEvents, None)

    # Set the logging level for this particular plugin. Let error and above
    # messages through but block info and lower. This is particularly usefull
    # for enabling and disabling debugging on a per plugin basis.
    reg.logger.setLevel(logging.INFO)

def shotgun_TS_DSD(sg, logger, event, args):
    """Flip downstream Tasks to 'rdy' if all of their upstream Tasks are 'fin'"""

    # we only care about Tasks that have been finalled
    if 'new_value' not in event['meta'] or event['meta']['new_value'] != 'fin':
        return
    else:
        ds_taskID = None
        change_status = False
        downstreamTasks = []
        upstreamTasks = []
        taskNotFinalList = []
        ds_taskList = []
        try:
            taskDict = event['entity']
            ds_filters = [
                ['upstream_tasks', 'is', taskDict],
                ['sg_status_list', 'is', 'wtg']
                ]
            ds_fields = ['upstream_tasks']
            downstreamTasks = sg.find("Task", ds_filters,ds_fields)
            for ds_task in downstreamTasks:
                ds_taskID = ds_task['id']
                if ds_taskID not in ds_taskList:
                    ds_taskList.append(ds_taskID)
                if 'upstream_tasks' in ds_task:
                    upstreamTasks = ds_task['upstream_tasks']
                    if upstreamTasks != []:
                        for us_task in upstreamTasks:
                            us_taskID = us_task.get('id')
                            us_filters = [['id','is',us_taskID]]
                            us_fields = ['sg_status_list']
                            us_task_status = sg.find("Task", us_filters,us_fields)[0]['sg_status_list']
                            if us_task_status != 'fin':
                                taskNotFinalList.append(us_taskID)

            if taskNotFinalList == [] or upstreamTasks == []:
                change_status = True
            else:
                change_status = False
            if change_status:
                if ds_taskList != []:
                    for ds_taskID in ds_taskList:
                        taskUpdateData = {'sg_status_list':'rdy'}
                        taskUpdate = sg.update ("Task",ds_taskID,taskUpdateData)
                        logger.info( "Set Task %s to 'rdy'" % ( ds_taskID ) )

        except Exception as error:
            logger.error('%s' % (error))
