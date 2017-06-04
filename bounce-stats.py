#!/usr/bin/env python

import sys
import argparse


def to_bool(value):
    if value == '1' or value == b'1':
        return True
    if value == '0' or value == b'0':
        return False
    raise NotImplementedError("Unknown boolean value %s" % repr(value))


def micro_to_mili(micro):
    return float(micro) / 1000


class SamplesSet(list):
    def direction(self, dir):
        return [s for s in self if s.direction == dir]

    def transition_counts(self, dir):
        return [s.transition_count for s in self.direction(dir)]

    def durations(self, dir):
        return [s.duration for s in self.direction(dir)]


class Switch(object):
    def __init__(self, start_state, start_moment):
        self.transitions = []
        self.start_state = to_bool(start_state)
        self.start_moment = int(start_moment)
        self.end_state = None

    def add_transition(self, nr, state, moment):
        assert int(nr) == len(self.transitions)
        self.transitions.append([state, int(moment)])

    @property
    def direction(self):
        assert self.start_state is not None and self.end_state is not None
        if self.start_state == True:
            d = "H"
        else:
            d = "L"
        if self.end_state == True:
            d += "H"
        else:
            d += "L"
        return d

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
    switches = SamplesSet()
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
    combined_switches = SamplesSet()
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


def sample_information(switches):
    directions = {}
    print("%d samples" % len(switches))
    for s in switches:
        dir = s.direction
        directions.setdefault(dir, 0)
        directions[dir] += 1
    for dir, count in directions.items():
        print("%s has %s samples" % (dir, count))


def create_stats(switches):
    direction_stats(switches, "LH")
    print("-"*5)
    direction_stats(switches, "HL")


def direction_stats(switches, dir):
    switch_count = len(switches.direction(dir))
    print("Total recorded %s switches: %d" % (dir, switch_count))
    most_transitions = max(switches.transition_counts(dir))
    least_transitions = min(switches.transition_counts(dir))
    avg_transitions = sum(switches.transition_counts(dir)) / switch_count
    print("%s transitions Most/Least/avg %g/%g/%g" % (dir, most_transitions, least_transitions, avg_transitions))
    slowest_switch  = max(switches.durations(dir))
    quickest_switch = min(switches.durations(dir))
    avg_switch      = sum(switches.durations(dir)) / switch_count
    print("%s switching Slowest/Quickest/avg %g/%g/%gms" % (dir, micro_to_mili(slowest_switch), micro_to_mili(quickest_switch),
          micro_to_mili(avg_switch)))
    duration_list = sorted(switches.durations(dir))
    pos90 = int(len(switches.direction(dir)) * 0.9)
    pos95 = int(len(switches.direction(dir)) * 0.95)
    pos99 = int(len(switches.direction(dir)) * 0.99)
    print("To debounce in 90%%/95%%/99%% of the cases, it should last %g/%g/%gms" % (
        micro_to_mili(duration_list[pos90]),
        micro_to_mili(duration_list[pos95]),
        micro_to_mili(duration_list[pos99]),
    ))

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
