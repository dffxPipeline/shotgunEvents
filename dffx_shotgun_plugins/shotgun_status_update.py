"""
For detailed information please see

http://shotgunsoftware.github.com/shotgunEvents/api.html
"""
import logging


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
    #eventFilter = {'Shotgun_Task_Change': ['sg_status_list']}
    matchEvents = {
        'Shotgun_Version_Change': ['sg_status_list']
    }
    reg.registerCallback('shotgunEventDaemon', '20e144217457a633c35fef9635ccb32c1a134d9f12060a0b496ec19f3095b603', shotgun_status_update, matchEvents, None)

    # Set the logging level for this particular plugin. Let error and above
    # messages through but block info and lower. This is particularly usefull
    # for enabling and disabling debugging on a per plugin basis.
    reg.logger.setLevel(logging.INFO)

def shotgun_status_update(sg, logger, event, args):
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
        statusUpdate = event['meta']['new_value']
        if statusUpdate != 'vwd' and statusUpdate != 'na':
            versionID=event['entity']['id']
            entityType=event['entity']['type']
            filters=[['id','is',versionID]]
            fields=['sg_task']

            versionTask=sg.find_one("Version",filters,fields)

            logger.info("%s" % str(versionTask))
        else:
            return


    #filters=['id','is',event['entity']['id']]
    #fields=['sg_task']

    #for item in sg.find("Version",filters,fields):
        #logger.info("%s" % str(item))

    #logger.info("%s" % str(versionFind))
