#!/usr/bin/env python
import os, sys, sqlite3
from unittest import TestCase, main
from pprint import pprint as pp

this_path = os.path.dirname(__file__)
try:
    import permset as dummy
except ImportError:
    sys.path.append(os.path.join(this_path, ".."))

from permset import Permset, process

class TestBasic(TestCase):
    def setUp(self):
        # permset.dump_db(con, "dump.sql")
        self.permset = Permset()
        self.permset.load_db(os.path.join(this_path, "testset-1.sql"))

    def tearDown(self):
        for fname in ("dump.sql", "r.txt", ".permset"):
            fname = os.path.join(this_path, fname)
            if os.path.exists(fname):
                os.remove(fname)

    def pp_patterns(self, patterns, expected, do_print):
        if do_print:
            print "\n"
            print "\n".join(map(str, patterns))
            print "----"
        self.assertEqual(len(patterns), len(expected))
        for p,e in zip(patterns, expected):
            self.assertEqual(p[:len(e)], e)

    def test_basic_files(self):
        self.permset.patterns = []
        patterns = self.permset.calculate_pattern("F")[0]
        self.pp_patterns(patterns, 
            [
              ('F', 'P', 'R' , 'rlujo|staff|rw-r--r--', '.',                             0, )
            , ('F', 'P', 'R' , 'rlujo|admin|rw-r--r--', './sites',                       1, )
            , ('F', 'S', None, 'rlujo|admin|rw-------', './sites/pak/local_settings.py', 2, )
            , ('F', 'S', None, 'rlujo|admin|rw-------', './sites/pak/local_settings.pyc',2, )
            , ('F', 'S', None, 'rlujo|admin|rw-------', './sites/ws/local_settings.py',  2, )
            , ('F', 'S', None, 'rlujo|admin|rw-------', './sites/ws/local_settings.pyc', 2, )
            ], False)
        cmds = self.permset.get_apply_patterns_commands(patterns)
        # pp(cmds)
        self.assertEqual(cmds,
           [u'chown -h rlujo                     $(find . -type f)',
            u'chgrp -h staff                     $(find . -type f)',
            u'chmod -h u+rw,u-x,g+r,g-wx,o+r,o-wx $(find . -type f)',
            u'chown -h rlujo                     $(find ./sites -type f)',
            u'chgrp -h admin                     $(find ./sites -type f)',
            u'chmod -h u+rw,u-x,g+r,g-wx,o+r,o-wx $(find ./sites -type f)',
            u'chown -h rlujo                     ./sites/pak/local_settings.py',
            u'chgrp -h admin                     ./sites/pak/local_settings.py',
            u'chmod -h u+rw,u-x,g-rwx,o-rwx      ./sites/pak/local_settings.py',
            u'chown -h rlujo                     ./sites/pak/local_settings.pyc',
            u'chgrp -h admin                     ./sites/pak/local_settings.pyc',
            u'chmod -h u+rw,u-x,g-rwx,o-rwx      ./sites/pak/local_settings.pyc',
            u'chown -h rlujo                     ./sites/ws/local_settings.py',
            u'chgrp -h admin                     ./sites/ws/local_settings.py',
            u'chmod -h u+rw,u-x,g-rwx,o-rwx      ./sites/ws/local_settings.py',
            u'chown -h rlujo                     ./sites/ws/local_settings.pyc',
            u'chgrp -h admin                     ./sites/ws/local_settings.pyc',
            u'chmod -h u+rw,u-x,g-rwx,o-rwx      ./sites/ws/local_settings.pyc']
            )

    def test_basic_dirs(self):
        # 2nd param is True/False for the case the parent pattern applies
        # recursively
        self.permset.patterns = []
        patterns = self.permset.calculate_pattern("D")[0]
        pp(patterns)
        self.pp_patterns(patterns, 
            [
              ('D', 'P', 'R', 'rlujo|staff|rwxr-xr-x', '.', 0)
            , ('D', 'P', 'R', 'rlujo|admin|rwxr-xr-x', './sites', 1)
            ], False)
        cmds = self.permset.get_apply_patterns_commands(patterns)
        # pp(cmds)
        self.assertEqual(cmds, 
           [u'chown -h rlujo                     $(find . -type d)',
            u'chgrp -h staff                     $(find . -type d)',
            u'chmod -h u+rwx,g+rx,g-w,o+rx,o-w   $(find . -type d)',
            u'chown -h rlujo                     $(find ./sites -type d)',
            u'chgrp -h admin                     $(find ./sites -type d)',
            u'chmod -h u+rwx,g+rx,g-w,o+rx,o-w   $(find ./sites -type d)']
           )

    def test_cmd_get(self):
        # dummy to test call
        # process([])
        # process(["--save", this_path])
        # process(["--set", this_path])
        # process(["--output", "r.txt", this_path])
        process([this_path])
        process([this_path, "--save"])
        process([this_path, "--set"])
        process([this_path, "--output", "r.txt"])

if __name__=="__main__":
    main()
    

