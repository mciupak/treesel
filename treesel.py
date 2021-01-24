# !/usr/bin/python
# coding=utf-8
# original code "https://gist.github.com/rygwdn/394885"

################################################################################
import os
import sys
import curses
import getopt
from curses import wrapper

################################################################################
__version__='0.1.5'
ESC = 27
result = ''
start = '.'
show_hidden = False
exclude = False
show_files = False


################################################################################
def pad(data, width):
    # ToDo: this won't work with UTF-8
    return data + ' ' * (width - len(data))


################################################################################
def list_dir_only(d):
    sds = []
    for sd in os.listdir(d):
        if os.path.isdir(os.path.join(d, sd)):
            if not show_hidden and sd not in ('.', '..') and sd[0] == '.':
                continue
            sds.append(sd)

    return sorted(sds)

class File:
    def __init__(self, name):
        self.name = name
        self.selected = False
    def render(self, depth, width):
        return pad('%s%s %s' % (' ' * 4 * depth, self.icon(),
                                os.path.basename(self.name)), width)
    def icon(self):
        if self.selected:
            return ' * '
        return '   '
    def traverse(self): yield self, 0
    def expand(self): pass
    def collapse(self): pass

################################################################################
class Dir(object):
# ==========================================================================
    def __init__(self, name):
        self.name = name
        if show_files:
            File.__init__(self, name)
        try:
            if show_files:
                self.kidnames = sorted(os.listdir(name))
            else:
                self.kidnames = list_dir_only(name)
        except:
            self.kidnames = None  # probably permission denied
        self.kids = None
        self.expanded = False
        self.selected = False

    # ==========================================================================
    def render(self, depth, width):
        return pad('%s%s %s' % (' ' * 4 * depth, self.icon(),
                                os.path.basename(self.name)), width)

    # ==========================================================================
    def children(self):
        if self.kidnames is None: return []
        if self.kids is None:
            self.kids = [factory(os.path.join(self.name, kid))
                         for kid in self.kidnames]
        return self.kids

    # ==========================================================================
    def icon(self):
        if self.selected:
            return '[*]'
        elif self.expanded:
            return '[-]'
        elif self.kidnames is None:
            return '[?]'
        elif self.children():
            return '[+]'
        else:
            return '[ ]'

    # ==========================================================================
    def expand(self):
        self.expanded = True

    # ==========================================================================
    def collapse(self):
        self.expanded = False

    # ==========================================================================
    def traverse(self):
        yield self, 0
        if not self.expanded: return
        for child in self.children():
            for kid, depth in child.traverse():
                yield kid, depth + 1


################################################################################
def factory(name):
    if not show_files or os.path.isdir(name):
        return Dir(name)
    else:
        return File(name)

################################################################################
def c_main(stdscr):
    cargo_cult_routine(stdscr)
    stdscr.nodelay(0)
    mydir = factory(start)
    mydir.expand()
    curidx = 3
    pending_action = None
    pending_save = False
    space = False
    excluded = set()

    while True:
        stdscr.clear()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
        line = 0
        offset = max(0, curidx - curses.LINES + 3)
        for data, depth in mydir.traverse():
            if line == curidx:
                global result
                stdscr.attrset(curses.color_pair(1) | curses.A_BOLD)
                if pending_action:
                    getattr(data, pending_action)()
                    pending_action = None
                elif pending_save:
                    if exclude:
                        result = excluded
                    else:
                        result = data.name
                    return
                elif space:
                    space = False
                    data.selected = not data.selected
                    if data.selected:
                        excluded.add(data.name)
                    else:
                        excluded.remove(data.name)

            else:
                stdscr.attrset(curses.color_pair(0))
            if 0 <= line - offset < curses.LINES - 1:
                stdscr.addstr(line - offset, 0,
                              data.render(depth, curses.COLS))
            line += 1
        stdscr.refresh()
        ch = stdscr.getch()
        if ch == curses.KEY_UP:
            curidx -= 1
        elif ch == curses.KEY_DOWN:
            curidx += 1
        elif ch == curses.KEY_PPAGE:
            curidx -= curses.LINES
            if curidx < 0: curidx = 0
        elif ch == curses.KEY_NPAGE:
            curidx += curses.LINES
            if curidx >= line: curidx = line - 1
        elif ch == curses.KEY_RIGHT:
            pending_action = 'expand'
        elif ch == curses.KEY_LEFT:
            pending_action = 'collapse'
        elif ch == ESC:
            return
        elif ch == ord('\n'):
            pending_save = True
        elif ch == ord(' '):
            space = True

        curidx %= line


################################################################################
def cargo_cult_routine(win):
    win.clear()
    win.refresh()
    curses.nl()
    curses.noecho()
    win.timeout(0)


################################################################################
def open_tty():
    saved_stdin = os.dup(0)
    saved_stdout = os.dup(1)
    os.close(0)
    os.close(1)
    stdin = os.open('/dev/tty', os.O_RDONLY)
    stdout = os.open('/dev/tty', os.O_RDWR)
    return saved_stdin, saved_stdout


################################################################################
def restore_stdio(saved_stdin, saved_stdout):
    os.close(0)
    os.close(1)
    os.dup(saved_stdin)
    os.dup(saved_stdout)


################################################################################
def usage(msg=None):
    """
    usage for this search program
    :param msg:
    :return:
    """
    if msg:
        sys.stderr.write('%s\n' % msg)
    print('''
usage: {0} [options] query_string
  query and search result from CVE
  options are:
    -h, --help : show this message
    -s, --show_hidden : show hidden directory
    -f, --show_files : show directories and files
    -e, --exclude : generate exclude.txt with files and directories selected by space key
'''.format(sys.argv[0]))
    sys.exit(1)


################################################################################
def main():
    global start
    global show_hidden
    global exclude
    global show_files
    saved_fds = (os.dup(0), os.dup(1))
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], "hsfe",
            ["help", "show_hidden", "show_files", "exclude"]
        )
        for o, a in opts:
            if o in ("-h", "--help"):
                usage()
            elif o in ("-s", "--show_hidden"):
                show_hidden = True
            elif o in ("-f", "--show_files"):
                show_files = True
            elif o in ("-e", "--exclude"):
                exclude = True
        if len(args) > 0:
            start = args[0]
        if not os.path.isdir(start):
            sys.stderr.write('Error: directory needed!\n')
            sys.exit(9)
        saved_fds = open_tty()
        wrapper(c_main)
        restore_stdio(*saved_fds)
        if exclude:
            with open('exclude.txt', 'w') as f:
                for r in result:
                    f.write("{}\n".format(r))
        else:
            print(result)
    except Exception as e:
        restore_stdio(*saved_fds)
        usage(str(e))


################################################################################
if __name__ == '__main__':
    main()