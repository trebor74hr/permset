permset
=======

Simple standalone utility script to manage \*nix permissions on file and directory trees based
on patterns.

Installation
------------
for admins - as a standalone script - go to some PATH visible dir and do:

    wget https://raw.github.com/trebor74hr/permset/master/permset/base.py -O permset && chmod u+x permset

for developers/devops/other - as a python package using [pip](http://www.pip-installer.org/en/latest/):

    pip install permset

try it out:

    permset

More details about installation options at the end of the page.

*Us it on your own risk - this sw is still in alpha stage*. 

Licence and disclaimer in [LICENCE](https://github.com/trebor74hr/permset/blob/master/LICENCE) 
file.

Requirements
------------

* \*nix (linux, osx, bsd, unix ...).
* Python 2.6+ (json module used).

Usage
-----

Usage:

    permset [options] [<dir>]

### Arguments:

* when dir is not specified, current folder is used (.)
* script uses dir/.permset to save/check against permission setup.
* when no options is set - script calculates patterns and prints them
  out.  If dir/.permset exists - calculated patterns and saved patterns
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
2. compare current permissions with saved patterns 
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
Some django project:

    user @ ~/env/proj/src/python/proj$ permset
    - - -  -------------------- ----------------------------------------
    F P R user1|staff|rw-r--r-- .
    F P R user1|admin|rw-r--r-- ./sites
    F S - user1|admin|rw------- ./sites/person/local_settings.py
    F S - user1|admin|rw------- ./sites/person/local_settings.pyc
    F S - user1|admin|rw------- ./sites/company/local_settings.py
    F S - user1|admin|rw------- ./sites/company/local_settings.pyc
    - - -  -------------------- ----------------------------------------
    D P R user1|staff|rwxr-xr-x .
    D P R user1|admin|rwxr-xr-x ./sites

    Call the script with --save option to save permission patterns.

Save the patterns:

    user @ ~/env/proj/src/python/proj$ permset --save
    Saved in ./.permset

Check current permissions with saved patterns:

    user @ ~/env/proj/src/python/proj$ permset
    Permission setup './.permset' matched.

Change permission for some file:

    user @ ~/env/proj/src/python/proj$ chmod u+x r.log

Check again - difference is noticed:

    user @ ~/env/proj/src/python/proj$ permset
    Permission differs from ./.permset setup.
    === Number of patterns differs (9!=10)

    Call the script with:
     - option --set - to reset everything to saved setup, or with
     - option --save - to overwrite setup with current permission patterns
     - option --verbose - to see details

See details:

    user @ ~/env/proj/src/python/proj$ permset --verbose
    Permission differs from ./.permset setup.
    Setup saved in ./.permset:
    - - -  -------------------- ----------------------------------------
    F P R user1|staff|rw-r--r-- .
    F P R user1|admin|rw-r--r-- ./sites
    F S - user1|admin|rw------- ./sites/person/local_settings.py
    F S - user1|admin|rw------- ./sites/person/local_settings.pyc
    F S - user1|admin|rw------- ./sites/company/local_settings.py
    F S - user1|admin|rw------- ./sites/company/local_settings.pyc
    - - -  -------------------- ----------------------------------------
    D P R user1|staff|rwxr-xr-x .
    D P R user1|admin|rwxr-xr-x ./sites

    Directory's current permission patterns:
    - - -  -------------------- ----------------------------------------
    F P R user1|staff|rw-r--r-- .
    F S - user1|staff|rwxr--r-- ./r.log
    F P R user1|admin|rw-r--r-- ./sites
    F S - user1|admin|rw------- ./sites/person/local_settings.py
    F S - user1|admin|rw------- ./sites/person/local_settings.pyc
    F S - user1|admin|rw------- ./sites/company/local_settings.py
    F S - user1|admin|rw------- ./sites/company/local_settings.pyc
    - - -  -------------------- ----------------------------------------
    D P R user1|staff|rwxr-xr-x .
    D P R user1|admin|rwxr-xr-x ./sites

    === Number of patterns differs (9!=10)

    Call the script with:
     - option --set - to reset everything to saved setup, or with
     - option --save - to overwrite setup with current permission patterns
     - option --verbose - to see details

Set all files permissions to match patterns:

    user @ ~/env/proj/src/python/proj$ permset --set
    Permission differs from ./.permset setup.
    === Number of patterns differs (9!=10)
    === Following commands needs to be executed to apply saved patterns:
    chown -h user1                     $(find . -type f)
    chgrp -h staff                     $(find . -type f)
    chmod -h u+rw,u-x,g+r,g-wx,o+r,o-wx $(find . -type f)
    ...
    chown -h user1                     $(find . -type d)
    chgrp -h staff                     $(find . -type d)
    chmod -h u+rwx,g+rx,g-w,o+rx,o-w   $(find . -type d)
    ...
    chmod -h u+rwx,g+rx,g-w,o+rx,o-w   $(find ./sites -type d)
    === Do you want to continue (y/n)? y
     chown -h user1                     $(find . -type f)
     ...
     chmod -h u+rwx,g+rx,g-w,o+rx,o-w   $(find ./sites -type d)
    === Done

Check again:

    user @ ~/env/proj/src/python/proj$ permset
    Permission setup './.permset' matched.


Logic behind patterns
---------------------
Shortly:

 * files and directory permissions are processed separately - due different x interpretation
 * patterns are searched for - recursively (R) and locally - current folder only
   (L). For the files/dirs that don't match current pattern - one special pattern entry for that file/dir is added (S).
 * patterns forumula: if more than 2/3 of files or directories have the same
   mark (user/group/permissions) that will become pattern

File .permset
------------------
File .permset contains saved patterns as list of lists in JSON format:

    [
     ["F", "P", "R", "user1|staff|rw-r--r--", ".", 0, [6, 7], [74, 101]]
    ,["F", "S", null, "user1|staff|rwxr--r--", "./permset", 0, null, null]
    ...
    ,["D", "P", "R", "user1|staff|rwxr-xr-x", ".", 0, [4, 5], [11, 14]]
    ,["D", "P", "R", "user1|admin|rwxr-xr-x", "./sites", 1, [2, 2], [2, 2]]
    ]
 
The file can be easily manually edited, as long as it is valid JSON format with valid permset options.

Internals and potential performance issues
---------------------------------------------------
The script is based on simple logic, done in [python](http://www.python.org/) programing language, internally uses python builtin [json](http://json.org/) parser and python's builtin [sqlite](https://sqlite.org/) db engine (as in-memory db). 

The script intended usage is for small to medium sized directory trees. For large ones the script probably won't perform well.

Development
-----------
Tests can be found in package file tests/tests.py.


Issue reporting
---------------
Report issue on [github](https://github.com/trebor74hr/permset/issues).

Licence and disclaimer
----------------------
Licence and disclaimer in [LICENCE](https://github.com/trebor74hr/permset/blob/master/LICENCE) file.

Installation options
--------------------------
### Easiest:
    
    pip install permset

### Standard python distutils
 * download latest release from http://pypi.python.org/pypi/permset
 * unpack & go to folder
 * run: python setup.py install

### Standalone script
Download, rename and make executable (in some PATH folder, e.g. ~/bin):

    wget https://raw.github.com/trebor74hr/permset/master/permset/base.py
    mv base.py permset
    chmod u+x permset

Try:

    ./permset

Contact
-------
If you want to contact author - mail can be found in 
[LICENCE](https://github.com/trebor74hr/permset/blob/master/LICENCE) file.
