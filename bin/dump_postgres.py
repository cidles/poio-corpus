# -*- coding: utf-8 -*-
#
# Poio Corpus
#
# Copyright (C) 2009-2013 Poio Project
# Author: Peter Bouda <pbouda@cidles.eu>
# URL: <http://www.poio.eu>
# For license information, see LICENSE.TXT

import sys
import os
import subprocess
import codecs
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

cmd_pgdump = "c:\\Program Files (x86)\\PostgreSQL\\8.4\\bin\\pg_dump.exe"

###################################### Main

def main(argv):
    config_file = os.path.join('..', 'config.ini')
    config = configparser.ConfigParser()
    config.read(config_file)

    prediction_dir = os.path.join("..", "build", "prediction")
    for iso_639_3 in config.options("LanguagesISOMap"):

    	print("Dumping database {0}...".format(iso_639_3))
        
        dump_file = os.path.join(prediction_dir, "{0}.pgdump".format(
            iso_639_3))

        f = codecs.open(dump_file, "w", "utf-8")
        proc = subprocess.call([cmd_pgdump, "-h", "localhost", "-U",
        	"postgres", "-c", iso_639_3], stdout=f)
       	f.close()


if __name__ == "__main__":
    main(sys.argv)