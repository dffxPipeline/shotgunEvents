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

def all_same(items):
    return all(x == items[0] for x in items)

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
    reg.logger.debug('Loading shotgun_CTS_PTS plugin.')

    configInfo = parseConfig()
    shotgunScriptName = configInfo[0]
    shotgunScriptKey = configInfo[1]

    matchEvents = {
        'Shotgun_Task_Change': ['sg_status_list']
    }
    reg.registerCallback(shotgunScriptName, shotgunScriptKey, shotgun_CTS_PTS, matchEvents, None)

    # Set the logging level for this particular plugin. Let error and above
    # messages through but block info and lower. This is particularly usefull
    # for enabling and disabling debugging on a per plugin basis.
    reg.logger.setLevel(logging.INFO)

def shotgun_CTS_PTS(sg, logger, event, args):
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
            valid_spawned_task_dict_list = []
            child_task_status_list = []
            TaskStatusUpdate = event['meta']['new_value']
            TaskID = event['entity']['id']
            event_task_filters = [['id', 'is', TaskID]]
            event_task_fields = ["sg_parent_task", "entity", "project"]
            parent_status_out = None

            event_task_dict = sg_find(sg, "Task", event_task_filters, event_task_fields)
            #logger.info("Current event_task_dict %s" % (str(event_task_dict)))
            if event_task_dict != None:
                sg_parent_task = event_task_dict.get("sg_parent_task", None)
                if sg_parent_task != None:
                    logger.info("Current event_task_dict %s" % (str(event_task_dict)))
                    logger.info("Current sg_parent_task %s" % (str(sg_parent_task)))
                    parent_task_id = sg_parent_task.get("id", None)
                    other_spawned_tasks_filter = [
                        ["entity", "is", event_task_dict.get("entity", None)],
                        ["project", "is", event_task_dict.get("project", None)]
                    ]
                    other_spawned_tasks_fields = ["sg_parent_task", "sg_status_list"]
                    other_spawned_task_dict_list = sg.find("Task", other_spawned_tasks_filter, other_spawned_tasks_fields)
                    #logger.info("Current other_spawned_task_dict %s" % (str(other_spawned_task_dict)))
                    if other_spawned_task_dict_list != None:
                        for task_dict in other_spawned_task_dict_list:
                            sg_parent_task = task_dict.get("sg_parent_task", None)
                            if sg_parent_task != None:
                                child_task_status = task_dict.get("sg_status_list", None)
                                child_task_status_list.append(child_task_status)
                                #valid_spawned_task_dict_list.append(task_dict)
                    logger.info("Current child_task_status_list %s" % (str(child_task_status_list)))

                    if "rev" in child_task_status_list:
                        parent_status_out = "rev"
                    elif "mn" in child_task_status_list:
                        parent_status_out = "mn"
                    elif "rnd" in child_task_status_list:
                        parent_status_out = "rnd"
                    elif "4k" in child_task_status_list:
                        parent_status_out = "4k"
                    elif "fdi" in child_task_status_list:
                        parent_status_out = "fdi"
                    else:
                        parent_status_out = "ip"

                    valid_fin_status_list = set(["fin", "omt"])
                    if "fin" in child_task_status_list:
                        if valid_fin_status_list >= set(child_task_status_list):
                            parent_status_out = "fin"
                        if all_same( child_task_status_list ) == True:
                            parent_status_out = "fin"
                    valid_fin_status_list = set(["if", "omt"])
                    if "if" in child_task_status_list:
                        if valid_fin_status_list >= set(child_task_status_list):
                            parent_status_out = "if"
                        if all_same( child_task_status_list ) == True:
                            parent_status_out = "if"
                    if "omt" in child_task_status_list:
                        if all_same( child_task_status_list ) == True:
                            parent_status_out = "omt"

                    if parent_status_out != None:
                        sg.update ("Task", parent_task_id, {'sg_status_list':str(parent_status_out)})
