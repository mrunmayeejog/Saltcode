'''
python script to return disk I/O statistics as a dict of raw tuples
'''
import re
import subprocess
from collections import namedtuple

disk_ntuple = namedtuple('disk', 'read_bytes write_bytes')
io_ntuple = namedtuple('io', 'read_iops write_iops read_thrput write_thrput')


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
        with open("/proc/partitions") as f:
            lines = f.readlines()[2:]
        for line in lines:
            _, _, _, name = line.split()
            partitions.append(name)
        return partitions

    retdict = {}
    partitions = get_partitions()
    with open("/proc/diskstats") as f:
        lines = f.readlines()
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
            raise ValueError("not sure how to interpret line %r" % line)

        if name in partitions:
            rbytes = rsector * SECTOR_SIZE
            wbytes = wsector * SECTOR_SIZE
            retdict[name] = disk_ntuple(rbytes, wbytes)
    return retdict


def io_stat():
    retiodict = {}
    # iostat works only >= Linux2.6+
    io = subprocess.Popen('iostat -dmx', shell=True, 
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    iostat, err = io.communicate()
    if err:
        print "err in iostat command"
        sys.exit(0)
    iodisk = re.split("\n", iostat)
    index = 3
    num_lines = len(iodisk)
    while index < num_lines:
        line = iodisk[index]
        if line:
            parts = re.split(r'\s+', line.strip())
            device, _, _, read_iops, write_iops, read_thrput, write_thrput, _, _, _, _, _, _, _ = parts[:14]
            retiodict[device] = io_ntuple(read_iops, write_iops, read_thrput, write_thrput)
            index = index + 1
        else:
            index = index + 1
    return retiodict
