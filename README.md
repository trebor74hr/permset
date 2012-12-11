permset
=======

Simple utility to manage \*nix permissions on file and directory trees based
on patterns.


Usage
-----

Usage:

    permset [options] [<dir>]


### Arguments:

* when <dir> is not specified, current folder is used (.)
* script uses <dir>/.permset to save/check against permission setup.
* when no options is set - script calculates patterns and prints them
  out.  If <dir>/.permset exists - calculated patterns and saved patterns
  are compared.

### Options

Options:

    -h, --help             show this help message and exit
    -o FILE, --output=FILE where to write output perm.setup to FILE. Option sets
                           save option too.
    -s, --save             save perm.setup to new file or overwrite existing
    -t, --set              set permissions by actual perm.setup
    -v, --verbose          verbose output


Common workflow 
---------------
Common workflow:

1. calculate permission patterns (permset), save them to root/.permset
   (permset --save)
2. When desired, compare current permissions with saved patterns 
   (permset), if any difference found, apply patterns (permset --set) 
   or overwrite existing patterns with new one (permset --save)


Pattern codes by columns
------------------------
Pattern codes by columns:

1. D - directory pattern, F - files pattern
2. P - is pattern, S - single file/directory
3. if pattern: R - recursive, L - current directory only
4. mark - user|group|permission
5. file/directory the entry applies to
6. (opt) file/directory depth - 0 is the root

Example session
---------------

