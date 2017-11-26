"""
Provides everything needed to preform auto updates of one or more files.
"""

import os
import urllib.request
import subprocess
import logging

update_logger = logging.getLogger('mlox.update')


def remote_file_changed(local_file, url):
    """
    Check if the local copy of a file has changed compared to a remote version.
    This currently cheats and just compares file sizes.
    """
    if not os.path.isfile(local_file):
        return True
    try:
        connection = urllib.request.urlopen(url)
    except Exception as e:
        update_logger.warning('Unable to connect to {0}, skipping update.'.format(url))
        update_logger.debug('Exception {0}.'.format(str(e)))
        return False

    local_size = os.stat(local_file).st_size
    update_logger.debug('Current size: {0}'.format(local_size))
    url_size = connection.info()['Content-Length']
    update_logger.debug('Downloadable size: {0}'.format(url_size))

    return int(url_size) != int(local_size)


def extract_via_7za(file_path, directory):
    """
    Extract the contents of a file to a directory, using 7za.
    WARNING:  This can and will silently overwrite files in the target directory.
    """
    cmd = ['7za', 'e', '-aoa', '-o{0}'.format(directory), file_path]
    update_logger.debug("Extracting via command %s", cmd)
    try:
        with open(os.devnull, 'w') as devnull:
            subprocess.check_call(cmd, stdout=devnull)
    except Exception as e:
        update_logger.error('Error while extracting from {0}'.format(file_path))
        update_logger.debug('Exception {0} while trying to execute command:  {0}'.format(str(e), cmd))
        return False
    return True


def extract_via_libarchive(file_path, directory):
    """
    Extract the contents of a file to a directory, using libarchive
    WARNING:  This can and will silently overwrite files in the target directory.
    """
    import libarchive
    abs_file_path = os.path.abspath(file_path)
    current_dir = os.path.abspath(os.getcwd())
    os.chdir(directory)
    try:
        libarchive.extract.extract_file(abs_file_path)
    except Exception as e:
        update_logger.error('Error while extracting from {0}'.format(file_path))
        update_logger.debug('Exception {0}'.format(str(e)))
        return False
    finally:
        os.chdir(current_dir)
    return True


def extract_file(file_path, directory):
    """
    Extract the contents of a file to a directory.
    Uses 7za or libarchive depending on what's available
    WARNING:  This can and will silently overwrite files in the target directory.
    """
    try:
        return extract_via_libarchive(file_path, directory)
    except ImportError:
        return extract_via_7za(file_path, directory)


def download_file(local_file, url):
    """Download a file from the internet"""
    try:
        urllib.request.urlretrieve(url, local_file)
    except Exception as e:
        update_logger.error('Unable to download {0}, skipping update.'.format(url))
        update_logger.debug('Error: {0}'.format(e))
        return False
    return True


def update_compressed_file(file_path, url, directory):
    """
    Check if a compressed file needs updating.
    If it does, download it, and extract it to a directory
    """
    if remote_file_changed(file_path, url):
        update_logger.info('Updating {0}'.format(file_path))
        if not download_file(file_path, url):
            return False
        update_logger.info('Downloaded {0}'.format(file_path))
        if not extract_file(file_path, directory):
            return False
        return True
    else:
        update_logger.info('No update necessary for file {0}'.format(file_path))
        return False
