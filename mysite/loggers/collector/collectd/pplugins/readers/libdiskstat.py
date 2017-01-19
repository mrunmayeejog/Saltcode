'''
python script to return disk I/O statistics as a dict of raw tuples
'''
import sys
from collections import namedtuple
import collectd
io_ntuple = namedtuple('io', 'read_count write_count read_bytes write_bytes read_mb write_mb')


def get_sector_size():
    try:
        with open(b"/sys/block/sda/queue/hw_sector_size") as f:
            return int(f.read())
    except (IOError, ValueError):
        # default
        return 512


def disk_io_counters():
    SECTOR_SIZE = get_sector_size()
    """Return disk I/O statistics for every disk installed on the
    system as a dict of raw tuples.
    """

    # determine partitions we want to look for
    def get_partitions():

        partitions = []
        try:
            with open("/proc/partitions") as f:
		lines = f.readlines()[2:]
        except IOError as e:
    	    collectd.debug("libdiskstat library: Could not read file '/proc/partitions'")
    	    return -1

        for line in lines:
            _, _, _, name = line.split()
            partitions.append(name)
        return partitions

    retdict = {}
    partitions = get_partitions()
    if partitions == -1:
	return -1

    try:
    	with open("/proc/diskstats") as f:
		lines = f.readlines()
    except IOError as e:
	collectd.debug("libdiskstat library: Could not read file '/proc/diskstats'")
        return -1

    for line in lines:
        fields = line.split()
        fields_len = len(fields)
        if fields_len == 15:
            # Linux 2.4
            name = fields[3]
            reads = int(fields[2])
            (reads_merged, rsector, rtime, writes, writes_merged,
             wsector, wtime, _, busy_time, _) = map(int, fields[4:14])
        elif fields_len == 14:
            # Linux 2.6+, line referring to a disk
            name = fields[2]
            (reads, reads_merged, rsector, rtime, writes, writes_merged,
             wsector, wtime, _, busy_time, _) = map(int, fields[3:14])
        elif fields_len == 7:
            # Linux 2.6+, line referring to a partition
            name = fields[2]
            reads, rsector, writes, wsector = map(int, fields[3:])
            rtime = wtime = reads_merged = writes_merged = busy_time = 0
        else:
            raise ValueError("libdiskstat library: not sure how to interpret line %r in /proc/diskstats" % line)

        if name in partitions:
            rbytes = rsector * SECTOR_SIZE
            wbytes = wsector * SECTOR_SIZE
            rmb = rbytes * float(0.000001)
            wmb = wbytes * float(0.000001)
            retdict[name] = io_ntuple(reads, writes, rbytes, wbytes, rmb, wmb)
    return retdict
