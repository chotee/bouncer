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

    def add_transition(self, nr, state, moment):
        assert int(nr) == len(self.transitions)
        self.transitions.append([state, int(moment)])

    @property
    def transition_count(self):
        return len(self.transitions)

    @property
    def duration(self):
        return self.transitions[-1][1]

    def combine_next_switch(self, next_switch):
        start_time_diff = next_switch.start_moment - self.start_moment
        for transition in next_switch.transitions:
            self.transitions.append([transition[0], transition[1]+start_time_diff])
        self.end_state = next_switch.end_state


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


def combine_switches(switches, config):
    prev_moment = 0
    combined_switches = []
    for switch in switches:
        start_moment_difference = switch.start_moment - prev_moment
        if start_moment_difference > config.settle_time or start_moment_difference < 0:
            # print("Event started at:", start_moment_difference,
            #       "transitions:", switch.transition_count,
            #       "duration:", switch.duration)
            combined_switches.append(switch)
        else:
            # print("Recombine with prev:", start_moment_difference)
            prev_switch = combined_switches[-1]
            prev_switch.combine_next_switch(switch)
            # print("Event now has tranitions:", prev_switch.transition_count, "duration:", prev_switch.duration)

        prev_moment = switch.start_moment + switch.duration
    return combined_switches


def create_stats(switches):
    switch_count = len(switches)
    print("Total recorded switches: %d" % switch_count)
    most_transitions = max([s.transition_count for s in switches])
    least_transitions= min([s.transition_count for s in switches])
    avg_transitions  = sum([s.transition_count for s in switches]) / switch_count
    print("Most/Least/avg transitions for a switch", most_transitions, least_transitions, avg_transitions)

    slowest_switch  = max([s.duration for s in switches])
    quickest_switch = min([s.duration for s in switches])
    avg_switch = sum([s.duration for s in switches]) / switch_count
    print("Slowest/Quickest/avg switch", slowest_switch, quickest_switch, avg_switch)


def main(argv):
    parser = argparse.ArgumentParser(description="Bounce data to statistics converter")
    parser.add_argument('datafiles', metavar="FILE", nargs=1, help="The bounce datafile")
    parser.add_argument('--settle-time', metavar='µsecs', help='number of microseconds between switches. Will recombine switches that are shorter then this', default=200000)
    config = parser.parse_args(argv[1:])

    for datafile in config.datafiles:
        with open(datafile, 'rb') as fd:
            switches = parse_file(fd, config)
            switches = combine_switches(switches, config)
            create_stats(switches)
if __name__ == '__main__':
    main(sys.argv)
