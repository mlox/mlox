# Update mlox_base.txt from the internet

UPDATE_FILE = 'mlox-data.7z'
UPDATE_URL = 'https://sourceforge.net/projects/mlox/files/mlox/' + UPDATE_FILE

import sys
import os
import urllib
import subprocess
import logging

update_logger = logging.getLogger('mlox.update')


#Download UPDATE_URL to the program's main directory, then extract its contents there
def update_mloxdata():
    program_path = os.path.realpath(sys.path[0])
    full_update_file = os.path.join(program_path,UPDATE_FILE)

    update_logger.info('Checking for database update...')
    try:
        d = urllib.urlopen(UPDATE_URL)
    except:
        update_logger.warning('Unable to connect to {0}, skipping mlox data update.'.format(UPDATE_URL))
        return

    #Compare file sizes to see if an update is needed or not
    if os.path.isfile(full_update_file):
        fsize = os.stat(full_update_file).st_size
        update_logger.debug('Current size: {0}'.format(fsize))
        dsize = d.info()['Content-Length']
        update_logger.debug('Downloadable size: {0}'.format(dsize))
        update = int(dsize) != int(fsize)
    else:
        update = 1

    if update:
        update_logger.info('Updating {0}'.format(full_update_file))
        try:
            d = urllib.urlretrieve(UPDATE_URL,full_update_file)
        except:
            update_logger.error('Unable to download {0}, skipping mlox data update'.format(UPDATE_URL))
            return

        update_logger.info('Downloaded {0}'.format(full_update_file))

        #Extract the file
        cmd = ['7za', 'e', '-aoa', '-o{0}'.format(program_path), full_update_file]
        try:
            devnull = open(os.devnull, 'w')
            subprocess.check_call(cmd, stdout=devnull)
        except Exception as e:
            update_logger.error('Error while extracting from {0}'.format(full_update_file))
            #update_logger.error('Exception {0} while trying to execute command:  {0}'.format(str(e),cmd))
            return
        update_logger.info('mlox_base.txt updated from {0}'.format(full_update_file))

    else:
        update_logger.info('No update necessary for file {0}'.format(full_update_file))
    return
