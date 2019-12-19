#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Photobooth - a flexible photo booth software
# Copyright (C) 2018  Balthasar Reuter <photobooth at re - web dot eu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from datetime import datetime
import logging
import os
from pkg_resources import get_distribution, DistributionNotFound

from .WorkerTask import WorkerTask
import piexif
from . import smugmug
session, album = smugmug.setup('photobooth.cfg')
#if not session:
#    logging.info('SmugMug upload is disabled.')
#else:
#    logging.info('SmugMug upload is enabled.')

try:
    __version__ = get_distribution('photobooth').version
except DistributionNotFound:
    __version__ = 'unknown_version'


class PictureSaver(WorkerTask):

    def __init__(self, basename):

        super().__init__()

        # Ensure directory exists
        dirname = os.path.dirname(basename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    def do(self, picture, filename):

        logging.info('Saving picture as %s', filename)
        with open(filename, 'wb') as f:
            f.write(picture.getbuffer())
        dt_now = datetime.now()
        exif_dict = piexif.load(filename)
        #exif_dict['0th'].pop(34665, None)  # remove old pointer
        exif_dict['0th'][piexif.ImageIFD.Make] = 'RaspberryPi'
        exif_dict['0th'][piexif.ImageIFD.Model] = 'RP_imx219'
        exif_dict['0th'][piexif.ImageIFD.Software] = f'Photobooth {__version__}'
        exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = dt_now.strftime('%Y:%m:%d %T')
        exif_dict['Exif'][piexif.ExifIFD.SubSecTimeOriginal] = dt_now.strftime('%f')[:2]
        exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = dt_now.strftime('%Y:%m:%d %T')
        exif_dict['Exif'][piexif.ExifIFD.SubSecTimeDigitized] = dt_now.strftime('%f')[:2]
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, filename)
        if session and 'shot' not in filename:
            smugmug.upload_image(session, album, filename)
