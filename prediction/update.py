# -*- coding: utf-8 -*-
#
# Poio Corpus
#
# Copyright (C) 2009-2013 Poio Project
# Author: Peter Bouda <pbouda@cidles.eu>
# URL: <http://media.cidles.eu/poio/>
# For license information, see LICENSE.TXT

# Works with Python 2 and 3, requires 64-bit Python

import sys
import os
import glob
import zipfile
import shutil
import codecs
import re
import pickle
from tempfile import mkdtemp
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import pressagio.tokenizer
import pressagio.dbconnector

###################################### Main

def main(argv):
    arg_iso = None
    if len(argv) > 1:
        arg_iso = argv[1]

    config_file = os.path.join('..', 'config.ini')
    config = configparser.ConfigParser()
    config.read(config_file)

    processed = dict()
    processed_file = os.path.join('..', 'build', 'processed.pickle')
    if os.path.exists(processed_file):
        with open(processed_file, 'rb') as f:
            processed = pickle.load(f)

    if 'prediction' not in processed:
        processed['prediction'] = dict()

    corpus_dir = os.path.abspath(os.path.join("..", "build", "corpus"))
    prediction_dir = os.path.join("..", "build", "prediction")
    for iso_639_3 in config.options("LanguagesISOMap"):
        
        if arg_iso and iso_639_3 != arg_iso:
            continue

        sql_file = os.path.join(prediction_dir, "{0}.sqlite".format(
            iso_639_3))

        if os.path.exists(sql_file):
            os.remove(sql_file)

        separators_file = os.path.join(
            "..", "build", "separators", "allchars.txt")
        s_f = codecs.open(separators_file, "r", "utf-8")
        separators = s_f.read()
        s_f.close()

        dictionary = []

        f = os.path.join(corpus_dir, "{0}wiki.zip".format(iso_639_3))
            
        _, filename = os.path.split(os.path.abspath(f))
        filebasename, _ = os.path.splitext(filename)

        print("Processing {0}".format(filename))

        try:
            tmp_path = mkdtemp()

            z = zipfile.ZipFile(f)
            z.extractall(tmp_path)

            text_files = glob.glob(os.path.join(
                tmp_path,"{0}*.txt".format(filebasename)))

            if len(text_files) != 1:
                print("  something is wrong with the archive. Exiting.")
                sys.exit(1)

            text_file = text_files[0]
            match = re.search(iso_639_3 + "wiki-(\d{8}).txt", text_file)
            if match:
                wiki_date = match.group(1)
            else:
                print("  Could not find date in corpus file. Exiting")
                sys.exit(1)

            if iso_639_3 in processed['prediction'] and \
                    int(processed['prediction'][iso_639_3]) >= int(wiki_date) and \
                    os.path.exists("{0}.zip".format(sql_file)):
                print "  Corpus files already processed, skipping."
                continue

            # build n-gramm statistics, requires pressagio:
            # http://github.com/cidles/pressagio
            for ngram_size in [1, 2, 3]:
                print("  Parsing {0} for cardinality {1}...".format(
                    text_file, ngram_size))

                cutoff = 0
                if ngram_size == 3 and os.path.getsize(text_file) > 20000:
                    cutoff = 1
                if ngram_size == 2 and os.path.getsize(text_file) > 100000:
                    cutoff = 1

                ngram_map = pressagio.tokenizer.forward_tokenize_file(
                    text_file, ngram_size, cutoff=cutoff)

                print("  Writing result to sqlite database...")
                pressagio.dbconnector.insert_ngram_map_sqlite(ngram_map,
                    ngram_size, sql_file, append=False, create_index=True)

                print("  Writing result to postgres database...")
                pressagio.dbconnector.insert_ngram_map_postgres(ngram_map,
                    ngram_size, iso_639_3, append=False, create_index=True,
                    lowercase=True)

        finally:
            try:
                shutil.rmtree(tmp_path)
            except WindowsError:
                pass

        print("  Zipping")
        myzip = zipfile.ZipFile(
            "{0}.zip".format(sql_file),
            'w',
            zipfile.ZIP_DEFLATED,
            True)
        myzip.write(sql_file, "{0}.sqlite".format(iso_639_3))
        myzip.close()
        os.remove(sql_file)

        processed['prediction'][iso_639_3] = wiki_date
        with open(processed_file, 'wb') as f:
            pickle.dump(processed, f)

        # append words to dictionary list
        #doc = ""
        #with codecs.open(text_file, "r", "utf-8") as f:
        #    doc = f.read()
        #dictionary.extend(_words_for_document(doc, separators))


        # write dictionary file
        #dict_file = os.path.join(prediction_dir, "{0}_dict.txt".format(
        #    iso_639_3))
        #with codecs.open(dict_file, "w", "utf-8") as f:
        #    f.write("\n".join(dictionary))

        # write config file
        config_template = u""
        with codecs.open("config_template.ini", "r", "utf-8") as f:
            config_template = f.read()
        config_file = os.path.join(prediction_dir, "{0}.ini".format(
            iso_639_3))
        with codecs.open(config_file, "w", "utf-8") as f:
            f.write(config_template.format(iso_639_3))

###################################### Helpers

def _words_for_document(doc, ignorechars):
    re_ignore_chars = re.compile(u"[{0}]".format(ignorechars))
    words = doc.split()
    words2 = set()

    for w in words:
        w = re_ignore_chars.sub("", w)

        if w == "":
            continue

        words2.add(w)

    return words2


if __name__ == "__main__":
    main(sys.argv)
