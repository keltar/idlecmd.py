#!/usr/bin/python

import psutil;
import re;
import argparse;
import os;

num_hits_cpu = 0;
num_hits_net = 0;
num_hits_disk = 0;

# default rules
cpu_rule = "";
net_rule = "";
disk_rule = "";
hits_to_trigger = 10;
verbose = False;

disk_last_sample = psutil.disk_io_counters();
net_last_sample = psutil.net_io_counters();

hits = 0;


def disk_megabytes():
	global disk_last_sample;
	sample = psutil.disk_io_counters();
	r = float(sample.write_bytes - disk_last_sample.write_bytes) / 1024 / 1024;
	w = float(sample.read_bytes - disk_last_sample.read_bytes) / 1024 / 1024;
	disk_last_sample = sample;
	return (r, w);

def net_megabytes():
	global net_last_sample;
	sample = psutil.net_io_counters();
	r = float(sample.bytes_recv - net_last_sample.bytes_recv) / 1024 / 1024;
	w = float(sample.bytes_sent - net_last_sample.bytes_sent) / 1024 / 1024;
	net_last_sample = sample;
	return (r, w);

def parse_rule(s):
	m = re.search("([><])([0-9.]+)([%Mm])", s);
	return (m.group(1), m.group(2), m.group(3));

def process_rule(rule, sample):
	if rule[0] == "<":
		return float(sample) < float(rule[1]);
	elif rule[0] == ">":
		return float(sample) > float(rule[1]);
	return False;

def step():
	global hits;
	global cpu_rule;
	global net_rule;
	global disk_rule;
	global hits_to_trigger;
	global verbose;

	cpu_sample = psutil.cpu_percent(interval=1);
	net_sample = net_megabytes();
	disk_sample = disk_megabytes();

	step_hit = True;
	cpu_hit = disk_hit = net_hit = True;

	if len(cpu_rule) > 0:
		rule = parse_rule(cpu_rule);
		cpu_hit = process_rule(rule, cpu_sample);
	if len(net_rule) > 0:
		rule = parse_rule(net_rule);
		# sum of incoming and outgoing
		net_hit = process_rule(rule, net_sample[0]+net_sample[1]);
	if len(disk_rule) > 0:
		rule = parse_rule(disk_rule);
		# sum of read and write
		disk_hit = process_rule(rule, disk_sample[0]+disk_sample[1]);

	step_hit = cpu_hit and net_hit and disk_hit;

	if step_hit:
		hits += 1;
	else:
		if hits > 0:
			print("resetting sample count (was %d)" % hits);
		hits = 0;

	if verbose:
		print("%d (cpu=%d, net=%d, disk=%d)" % (hits, cpu_hit, net_hit, disk_hit));

	return (hits >= hits_to_trigger);

# args
parser = argparse.ArgumentParser();
parser.add_argument('-c', "--cpu", action="store_true");
parser.add_argument('-d', "--disk", action="store_true");
parser.add_argument('-n', "--net", action="store_true");
parser.add_argument("--cpu-rule", default="<20%");
parser.add_argument("--disk-rule", default="<1M");
parser.add_argument("--net-rule", default="<0.2M");
parser.add_argument('-t', "--time", help="sample range, in seconds");
parser.add_argument('-r', "--run", help="command to run");
parser.add_argument("--exit-code", type=int, default=0);
parser.add_argument('-v', "--verbose", action="store_true");
args = parser.parse_args();

if args.cpu:
	cpu_rule = args.cpu_rule;
if args.net:
	net_rule = args.net_rule;
if args.disk:
	disk_rule = args.disk_rule;

hits_to_trigger = int(args.time) if args.time != None else hits_to_trigger;
verbose = bool(args.verbose);
command = args.run;
exit_code = args.exit_code;

# main loop
try:
	while True:
		if step():
			if verbose:
				print("triggered\n");

			if command != None and len(command) > 0:
				os.system(command);
			os.exit(exit_code);
except KeyboardInterrupt:
	print("interrupt received, stopping");
