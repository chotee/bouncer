#!/usr/bin/env python

import sys
import argparse


def to_bool(value):
    if value == '1' or value == b'1':
        return True
    if value == '0' or value == b'0':
        return False
    raise NotImplementedError("Unknown boolean value %s" % repr(value))


class Switch():
    def __init__(self, start_state, start_moment):
        self.transitions = []
        self.start_state = to_bool(start_state)
        self.start_moment = int(start_moment)
        self.end_state = None
        print('Switch at %s' % self.start_moment)

    def add_transition(self, nr, state, moment):
        assert int(nr) == len(self.transitions)
        self.transitions.append([state, int(moment)])


def start_decoder(line, switches):
    parts = line.split(b":")
    if parts[0] != b"START":
        return None
    switch = Switch(start_state=parts[1], start_moment=parts[2])
    switches.append(switch)
    return switch


def line_decoder(line, switch):
    parts = line.split(b":")
    if parts[0] == b"END":
        switch.end_state = to_bool(parts[1])
        return None
    else:
        nr, state, moment = parts
        switch.add_transition(nr, state, moment)
        return switch


def parse_file(fd, config):
    switches = []
    curr_switch = None
    for line in line_reader(fd):
        if curr_switch is None:
            curr_switch = start_decoder(line, switches)
        else:
            curr_switch = line_decoder(line, curr_switch)
    return switches

def line_reader(fd):
    for line in fd.readlines():
        yield line.strip()


def main(argv):
    parser = argparse.ArgumentParser(description="Bounce data to statistics converter")
    parser.add_argument('datafiles', metavar="FILE", nargs=1, help="The bounce datafile")
    config = parser.parse_args(argv[1:])

    for datafile in config.datafiles:
        with open(datafile, 'rb') as fd:
            switches = parse_file(fd, config)

if __name__ == '__main__':
    main(sys.argv)
