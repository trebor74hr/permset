#!/usr/bin/env python
# coding:utf-8
"""Simple utility to manage \*nix permissions on file and directory trees
   based on patterns

   Details: https://github.com/trebor74hr/permset
   LICENCE: BSD like - details in 
            https://github.com/trebor74hr/permset/blob/master/LICENCE
   Copyright (c) 2012, Robert Lujo, Zagreb, Croatia, mail in LICENCE file.
"""
import os, sys, sqlite3
import pwd, grp, stat 
import json
from pprint import pprint as pp
from optparse import OptionParser
from codecs import open

# ------------------
# Utils
# ------------------

def ask_user_yes_no(title):
    while True:
        ans = raw_input(title+" (y/n)? ")
        if ans.lower() in ("y", "n"):
            ans = (ans.lower()=="y")
            break
    return ans

# ------------------

def get_perm(name):
    """ inspired by stackoverflow answer on the similar problem """
    stat_info = os.lstat(name)
    mode = stat_info.st_mode

    uid = stat_info.st_uid
    gid = stat_info.st_gid
    user = pwd.getpwuid(uid)[0]
    group = grp.getgrgid(gid)[0]

    perms = {}
    mask = []
    for who,who_is in (("usr", user), ("grp", group), ("oth", None)):
        perms[who] = {"is" : who_is, "perms" : {}}
        for what in "r", "w", "x":
            has_perm = bool(mode & getattr(stat,"S_I"+what.upper()+who.upper()))
            perms[who]["perms"][what] = has_perm
            mask.append(what.lower() if has_perm else "-")
    mask = "".join(mask)
    perms["mask"] = mask
    return (user, group, mask, perms)

# ------------------

def to_unicode(s, force=False):
    if isinstance(s, str):
        s = unicode(s, "utf-8")
    elif force:
        if s is True: 
            s = "+"
        elif s in (False, None): 
            s = "-"
        else:
            s = unicode(s)
    return s

# -------------
# consts
# -------------

PERMSET_FILE = ".permset"

# -------------
# Permset - main class 
# -------------

class Permset(object):

    def __init__(self):
        self.con = sqlite3.connect(":memory:")

    def fill_db(self, root_dir):
        root_dir = os.path.abspath(root_dir)
        cur = self.con.cursor()
        cur.execute("create table perm(mark varchar, depth int, name varchar, type varchar)")

        def insert_it(name_abs, type):
            # NOTE: perms not used
            user, group, mask, perms = get_perm(name_abs)
            mark = u"%s|%s|%s" % (user, group, mask)
            assert mark.count("|")==2
            assert name_abs.startswith(root_dir), name_abs
            name_rel = "./"+name_abs[len(root_dir):].lstrip("/")
            depth = name_rel[1:].lstrip("/").rstrip("/").count("/")
            try:
                cur.execute("insert into perm values(?,?,?,?)", 
                            (mark, depth, name_rel, type))
            except Exception, e:
                print("error by inserting: %s" % [mark, depth, name_rel, type])
                raise

        for root, dnames, fnames in os.walk(root_dir):
            for names, type in ((dnames, "D"), (fnames, "F")):
                for name in names:
                    if root!=root_dir and name==PERMSET_FILE:
                        print("Nesting not supported - found %s in %s. Terminating.\nRemove the file or run the script there." % (
                               name, root))
                        return False
                    name_abs = to_unicode(os.path.abspath(os.path.join(root, name)))
                    insert_it(name_abs, type)
        cur.execute("create index idx_perm_name_depth on perm(name, depth)")
        cur.execute("create index idx_perm_type_name  on perm(type, name)")
        return True

    def dump_db(self, fname):
        with open(fname, 'w') as f:
            for line in self.con.iterdump():
                f.write('%s\n' % line)

    def load_db(self, fname):
        content = open(fname, 'r').read()
        cur = self.con.cursor()
        try:
            cur.execute("drop table perm")
        except: 
            pass
        self.con.executescript(open(fname).read())

    def get_best_mark(self, root_term, type, depth):
        cur = self.con.cursor()
        depth_term = "and depth=%s" % depth if depth is not None else ""
        cur.execute("""select count(*) from perm where name like ? 
                     and type=? %s""" % depth_term, 
                    (root_term,type))
        cnt_all = cur.fetchone()[0]
        if cnt_all:
            cur.execute(
                """select count(*), mark 
                   from perm where name like ? and type=? %s
                   group by mark order by 1 desc, 2
                """ % depth_term, (root_term,type))
            cnt_main, mark_main = cur.fetchone()
            cur.close()
            mark_main = str(mark_main)
            # add one - gives better results 
            # example: when .permset is added after
            ratio = round((cnt_main+1)/(cnt_all+0.0),5)
        else:
            cnt_main = mark_main = ratio  = None
        return cnt_main, cnt_all, mark_main, ratio

    def calculate_pattern(self, type, depth=0, root=None, parent_recursive_pattern=None):
        """ Algorithm - obsolete: 
           guess pattern of current dir
           if there is a pattern (more than 66% are have perms)
             - check if the same pattern is recursive
             - if it is recursive
                 - save as an recursive pattern 
                 - call recursivelly for all child dirs with the pattern as
                   input arg
             - if the pattern is not recursive
                 - write a local dir pattern
                 - call recursivelly for all child dirs with no recursive
                   pattern as arg
           check rest of files in dirs
             - if dir has pattern and pattern is appliable - do nothing
             - other cases - write single entry "pattern"
        """
        type=str(type)
        is_recursive_pattern = False
        if root is None:
            root = "."
            for item in self.patterns:
                assert item[0]!=type
        patterns = self.patterns

        root_term = root+"/"+"%"
        minimum = (2/3.)

        cnt_main1, cnt_all1, mark_main1, ratio1 = self.get_best_mark(root_term, 
                                                    type, depth=depth)
        cnt_main2, cnt_all2, mark_main2, ratio2 = self.get_best_mark(root_term, 
                                                    type, depth=None)
        local_pattern = None

        if mark_main2 and ratio2 >= minimum:
            local_pattern = mark_main2
            if parent_recursive_pattern!=mark_main2:
                patterns.append((type, "P", "R", mark_main2, root, depth, 
                    [cnt_main1, cnt_all1] if ratio1>=minimum else None, 
                    [cnt_main2, cnt_all2]))
                parent_recursive_pattern=mark_main2
            elif parent_recursive_pattern:
                assert parent_recursive_pattern==mark_main2
            is_recursive_pattern = True

        if mark_main1 and (local_pattern is None or mark_main1!=mark_main2) and ratio1 >= minimum:
            local_pattern = mark_main1
            patterns.append((type, "P", "L", mark_main1, root, depth, [cnt_main1, cnt_all1], None))

        cur = self.con.cursor()
        cur.execute("""select mark, name, type from perm 
                       where name like ? and depth=? 
                       order by type desc, name""", 
                    (root_term, depth))
        rows = cur.fetchall()
        cur.close()
        for mark, name, type_this in rows:
            is_exception = type==type_this and not (
                            local_pattern and mark==local_pattern)
            if type_this=="D":
                parent_pattern = parent_recursive_pattern
                dummy, became_recursive_pattern = self.calculate_pattern(type, depth+1, name, 
                                                    parent_pattern)
                if is_exception and became_recursive_pattern:
                    is_exception = False

            if is_exception:
                patterns.append((type, "S", None, mark, name, depth, None, None))

        return patterns, is_recursive_pattern

    def calculate_patterns_all(self):
        self.patterns = []
        self.calculate_pattern("F")
        self.calculate_pattern("D")
        return self.patterns

    # list of class and static methods - I was in the static/class method's
    # moode :)

    @classmethod
    def get_diff(cls, patterns, patterns_saved):
        diff = ""
        if len(patterns_saved)!=len(patterns):
            diff = "Number of patterns differs (%s!=%s)" % (
                    len(patterns_saved), len(patterns)
                    )
            return diff

        for ps, pg in zip(patterns_saved, patterns):
            #  0    1    2     3     4     5      6     7
            # ("D", "S", type, mark, name, depth, None, None))
            ps, pg = ps[:6], pg[:6]
            ps, pg = map(tuple, (ps, pg))
            if ps!=pg:
                diff = "First diff:\n%s\n<>\n%s" % (
                       cls.pp_pattern_line(ps), 
                       cls.pp_pattern_line(pg))
                break
        return diff

    @classmethod
    def pp_pattern_line(cls, patt):
        return " ".join([to_unicode(p, True) for p in patt[:-1]]) + " [%s]" % patt[-1]

    @staticmethod
    def pp_patterns(patterns):
        lens = [len(c[3]) for c in patterns]
        if lens:
            mark_len = max(lens)
        else:
            mark_len = 20
        fmt = "%%s %%s %%s %%%ds %%s" % mark_len
        patts = patterns
        type_prev = None
        for patt in patts:
            patt = [to_unicode(p, True) for p in patt]
            type, pt, ty, mark, name, depth, s1, s2 = patt
            if type!=type_prev:
                print(fmt % ("-", "-", "-", "-"*20, "-"*40))
            print(fmt % (type, pt, ty, mark, name))
            type_prev = type

    @staticmethod
    def get_perm_str(perm):
        perm_str = []
        for i,who in enumerate(("u", "g", "o")):
            ops = {"-" : [], "+": []}
            for j,what in enumerate(("r", "w", "x")):
                pe = perm[i*3+j]
                op = "-" if pe=="-" else "+"
                if pe!="-": assert what==pe, "%s!=%s" % (what, pe)
                ops[op].append(what)
            for op in ("+", "-"):
                if ops[op]:
                    perm_str.append(who+op+"".join(ops[op]))
        return ",".join(perm_str)

    @classmethod
    def get_apply_pattern_command(cls, patt):
        """ using find in ch* commands is inspired by:
            http://serverfault.com/questions/104804/chmod-applying-different-permissions-for-files-vs-directories
        """
        cmds = []
        type, pt, ty, mark, name, depth, s1, s2 = patt
        user, group, perm = mark.split("|")
        perm_str = cls.get_perm_str(perm)
        options = []
        # -h If the file is a symbolic link, the group ID of the link itself
        #    is changed rather than the file that is pointed to.
        options.append("-h")
        target = name
        if pt=="P":
            if ty=="R":
                target = u"$(find %s -type %s)" % (name, type.lower())
            else:
                assert ty=="L"
                target = u"$(find %s -depth 1 -type %s)" % (name, type.lower())
        else:
            assert pt=="S"
            assert ty is None
        cmds.append(u"chown %s %-25s %s" % (" ".join(options), user,     target))
        cmds.append(u"chgrp %s %-25s %s" % (" ".join(options), group,    target))
        cmds.append(u"chmod %s %-25s %s" % (" ".join(options), perm_str, target))
        return cmds

    @classmethod
    def get_apply_patterns_commands(cls, patterns):
        return [c for patt in patterns for c in cls.get_apply_pattern_command(patt)]

    @staticmethod
    def load_patterns_saved(output):
        return json.load(open(output, "r", "utf-8"))

    @staticmethod
    def check_before_set(patts):
        def report_err(err_msg):
            print(u"%s. Please:\n - fix setup file %s manually or\n - save new one with --save option" % (
                   err_msg, PERMSET_FILE))
            return False
        for type, pt, ty, mark, name, depth, s1, s2 in patts:
            if pt=="P":
                type2 = "D"
            else:
                type2 = type
            what = "directory" if type2=="D" else "file"
            check_fun = os.path.isdir if type2=="D" else os.path.isfile
            if not os.path.exists(name):
                return report_err("%s '%s' not found." % (what.title(), name))
            if not check_fun(name):
                return report_err("'%s' is not a %s" % (name, what))
        return True

    @staticmethod
    def dump_patterns(patterns):
        """ more human readable than default json.dumps """
        return u"[\n %s\n]" % u"\n,".join(
                 [json.dumps(patt) for patt in patterns])

# -------------

def print_usage(parser, m):
    if m:
        print ("Error: %s\n" % m)
    print parser.format_help()
    return False

# -------------

def process(argv):
    """ main program """

    parser = OptionParser(usage="""Usage: %prog [options] [<dir>]

Simple utility to manage *nix permissions on file and directory trees based
on patterns. 

Common workflow: 
    a) calculate permission patterns (%prog), save them to root/.permset
    (%prog --save)
    b) When desired, compare current permissions with saved patterns 
    (%prog), if any difference found, apply patterns (%prog --set) 
    or overwrite existing patterns with new one (%prog --save)

Arguments:
    - when <dir> is not specified, current folder is used (.)
    - script uses <dir>/.permset to save/check against permission setup.
    - when no options is set - script calculates patterns and prints them
      out.  If <dir>/.permset exists - calculated patterns and saved patterns
      are compared.

Pattern codes by columns:
    1. D - directory pattern, F - files pattern
    2. P - is pattern, S - single file/directory
    3. if pattern: R - recursive, L - current directory only
    4. mark - user|group|permission
    5. file/directory the entry applies to
    6. (opt) file/directory depth - 0 is the root""")
    parser.add_option("-o", "--output", dest="output",
                      help="where to write output perm.setup to FILE. Option sets save option too.", 
                      default=None, metavar="FILE")
    parser.add_option("-s", "--save",
                      action="store_true", dest="save", default=False,
                      help="save perm.setup to new file or overwrite existing")
    parser.add_option("-t", "--set",
                      action="store_true", dest="set", default=False,
                      help="set permissions by actual perm.setup")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="verbose output")

    (options, args) = parser.parse_args(args=argv)

    if options.set and options.save:
        print("Error: options set and save should't be used together")
        return False

    if len(args)==1:
        root_dir = args[0]
    elif len(args)==0:
        root_dir = "."
    else:
        print("Error: Invalid number of arguments")
        return False

    if not os.path.isdir(root_dir):
        print("'%s' is not a directory" % root_dir)
        return False

    permset = Permset()
    if options.output:
        output = options.output 
        options.save = True
    else:
        output = os.path.join(root_dir, PERMSET_FILE)

    if not permset.fill_db(root_dir):
        return False

    # NOTE: nice when testing
    #   permset.dump_db("dump.sql")
    #   permset.load_db("dump.sql")

    patterns = permset.calculate_patterns_all()

    if options.save:
        if options.verbose:
            permset.pp_patterns(patterns)
        open(output, "w", "utf-8").write(permset.dump_patterns(patterns))
        print("Saved in %s" % output)
    else:
        if os.path.exists(output):
            patterns_saved = permset.load_patterns_saved(output)
            diff = permset.get_diff(patterns, patterns_saved)
            if options.set:
                cmds = permset.get_apply_patterns_commands(patterns_saved)

            if diff:
                print("Permission differs from %s setup." % output)
                if options.verbose:
                    print("Setup saved in %s:" % output)
                    permset.pp_patterns(patterns_saved)
                    print("\nDirectory's current permission patterns:")
                    permset.pp_patterns(patterns)
                    print("\n")
                print(u"=== "+diff)
                if options.set:
                    # TODO: put in function
                    if not permset.check_before_set(patterns_saved):
                        return False
                    print("=== Following commands needs to be executed to apply saved patterns:")
                    print "\n".join(cmds)
                    if not ask_user_yes_no("=== Do you want to continue"):
                        return False

                    for cmd in cmds:
                        try:
                            print(" %s" % cmd)
                            os.system(cmd)
                        except Exception, e:
                            if not ask_user_yes_no("=== Error:%s\n=== Do you want to continue" % (e, )):
                                return False
                    print("=== Done")
                else:
                    print("\nCall the script with:\n - option --set - to reset everything to saved setup, or with\n - option --save - to overwrite setup with current permission patterns\n - option --verbose - to see details")
            else:
                if options.verbose:
                    print("Setup:")
                    permset.pp_patterns(patterns_saved)
                    print("===")
                    if options.set:
                        print("=== Following commands can be used to apply patterns:")
                        print "\n".join(cmds)
                        print("===")

                if options.set:

                    print("Permission setup '%s' matched, nothing to set." % output)
                else:
                    print("Permission setup '%s' matched." % output)
        else:
            if options.set:
                print("Permission setup file %s not found." % output)
            else:
                permset.pp_patterns(patterns)
            print("\nCall the script with --save option to save permission patterns.")

    return True

if __name__=="__main__":
    process(sys.argv[1:])


# obsolete:
# NOTE: umask in bitwise mode works opposite as expected - what is denied
# NOTE: chmod for dir sets x but not for files, X is special that can solve
#       this

# def has_perm(name):
#     try:
#         if os.isdir(name):
#             os.listdir(name)
#         elif os.isfile(name):
#             open(name)
#         else:
#             raise Exception("unknown file object type: %s" % name)
#     except IOError as e:
#         if e.errno == errno.EACCES:
#             return False
#         raise
#     return True
# 
# def get_perm_num(name):
#     """ follow symlinks """
#     return str(oct(os.lstat(name).st_mode & 0777))

