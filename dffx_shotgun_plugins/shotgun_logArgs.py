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
        configFileName = 'shotgun_Logging.conf'
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
    reg.logger.debug('Loading shotgun_Logging plugin.')

    configInfo = parseConfig()
    shotgunScriptName = configInfo[0]
    shotgunScriptKey = configInfo[1]

    eventFilter = None
    reg.registerCallback(shotgunScriptName,shotgunScriptKey, shotgun_logArgs, eventFilter, None)

    # Set the logging level for this particular plugin. Let error and above
    # messages through but block info and lower. This is particularly usefull
    # for enabling and disabling debugging on a per plugin basis.
    reg.logger.setLevel(logging.INFO)


def shotgun_logArgs(sg, logger, event, args):
    """
    A callback that logs its arguments.

    @param sg: Shotgun instance.
    @param logger: A preconfigured Python logging.Logger object
    @param event: A Shotgun event.
    @param args: The args passed in at the registerCallback call.
    """
    logger.info("%s" % str(event))
