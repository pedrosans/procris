"""
Kupfer code from: https://github.com/kupferlauncher/kupfer/blob/feca5b98af28d77b8a8d3af60d5782449fa71563/kupfer/desktop_launch.py
"""
import os

from gi.repository import Gtk, Gdk, Gio, GLib

import xdg.DesktopEntry
import xdg.Exceptions

def replace_format_specs(argv, location, desktop_info, gfilelist):
    """
    http://standards.freedesktop.org/desktop-entry-spec/latest/ar01s06.html

    Replace format specifiers

    %% literal %
    %f file
    %F list of files
    %u URL
    %U list of URLs
    %i --icon <Icon key>
    %c Translated name
    %k location of .desktop file

    deprecated are removed:
    %d %D %n %N %v %m

    apart from those, all other.. stay and are ignored
    Like other implementations, we do actually insert
    a local path for %u and %U if it exists.

    Return (supports_single, added_at_end, argv)

    supports_single: Launcher only supports a single file
                     caller has to re-call for each file
    added_at_end:    No format found for the file, it was added
                     at the end
    """
    supports_single_file = False
    files_added_at_end = False
    class Flags(object):
        did_see_small_f = False
        did_see_large_f = False

    fileiter = iter(gfilelist)

    def get_file_path(gfile):
        if not gfile:
            return ""
        return gfile.get_path() or gfile.get_uri()

    def get_next_file_path():
        try:
            f = next(fileiter)
        except StopIteration:
            return ""
        return get_file_path(f)

    def replace_single_code(key):
        "Handle all embedded format codes, including those to be removed"
        deprecated = set(['%d', '%D', '%n', '%N', '%v', '%m'])
        if key in deprecated:
            return ""
        if key == "%%":
            return "%"
        if key == "%f" or key == "%u":
            if Flags.did_see_large_f or Flags.did_see_small_f:
                warning_log("Warning, multiple file format specs!")
                return ""
            Flags.did_see_small_f = True
            return get_next_file_path()

        if key == "%c":
            return gtk_to_unicode(desktop_info["Name"] or location)
        if key == "%k":
            return location
        else:
            return None

    def replace_array_format(elem):
        """
        Handle array format codes -- only recognized as single arguments
        
        Return  flag, arglist
        where flag is true if something was replaced
        """
        if elem == "%U" or elem == "%F":
            if Flags.did_see_large_f or Flags.did_see_small_f:
                warning_log("Warning, multiple file format specs!")
                return True, []
            Flags.did_see_large_f = True
            return True, list(filter(bool,[get_file_path(f) for f in gfilelist]))
        if elem == "%i":
            if desktop_info["Icon"]:
                return True, ["--icon", desktop_info["Icon"]]
            return True, []
        else:
            return False, elem

    def two_part_unescaper(s, repfunc):
        """
        Handle embedded format codes

        Scan @s two characters at a time and replace using @repfunc
        """
        if not s:
            return s
        def _inner():
            it = iter(zip(s, s[1:]))
            for cur, nex in it:
                key = cur+nex
                rep = repfunc(key)
                if rep is not None:
                    yield rep
                    # skip a step in the iter
                    try:
                        next(it)
                    except StopIteration:
                        return
                else:
                    yield cur
            yield s[-1]
        return ''.join(_inner())

    new_argv = []
    for x in argv:
        if not x:
            # the arg is an empty string, we don't need extra processing
            new_argv.append(x)
            continue
        succ, newargs = replace_array_format(x)
        if succ:
            new_argv.extend(newargs)
        else:
            arg = two_part_unescaper(x, replace_single_code)
            if arg:
                new_argv.append(arg)
    
    if len(gfilelist) > 1 and not Flags.did_see_large_f:
        supports_single_file = True
    if not Flags.did_see_small_f and not Flags.did_see_large_f and len(gfilelist):
        files_added_at_end = True
        new_argv.append(get_next_file_path())

    return supports_single_file, files_added_at_end, new_argv

