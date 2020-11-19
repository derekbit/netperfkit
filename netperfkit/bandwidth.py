import subprocess

class Error(Exception):
    pass

def apply_multiplier(quantity, multiplier):
    """Given a quantity and multiplier of 'Xbits/sec', return bits/sec."""

    MULTIPLIERS={
        'bits/sec': 1.0e0,
        'Kbits/sec': 1.0e3,
        'Mbits/sec': 1.0e6,
        'Gbits/sec': 1.0e9,
    }

    if multiplier not in MULTIPLIERS:
        raise Error('Could not parse multiplier %s' % multiplier)
    return float(quantity) * MULTIPLIERS[multiplier]


def _parse_one_tcp_line(line):
    """Parses a line of TCP output, returns bandwidth.
    Args:
        line:  a line like "[  3]  0.0- 5.2 sec  0.06 MBytes  0.10 Mbits/sec"
    """
    tcp_tokens = line.split()
    if len(tcp_tokens) >= 6 and 'bits/sec' in tcp_tokens[-1]:
        return apply_multiplier(tcp_tokens[-2], tcp_tokens[-1])
    else:
        raise Error('Could not parse TCP line')


def _parse_tcp_output(lines):
    """Parses the following and returns a single dictionary with
    uplink throughput, and, if available, downlink throughput.
    ------------------------------------------------------------
    Client connecting to localhost, TCP port 5001
    TCP window size: 49.4 KByte (default)
    ------------------------------------------------------------
    [  3] local 127.0.0.1 port 57936 connected with 127.0.0.1 port 5001
    [ ID] Interval       Transfer     Bandwidth
    [  3]  0.0-10.0 sec  2.09 GBytes  1.79 Gbits/sec
    """
    perf = {}

    uplink = _parse_one_tcp_line(lines[-2])
    perf['uplink_throughput'] = uplink

    return perf


def _parse_one_udp_line(line, prefix):
    udp_tokens = line.replace('/', ' ').split()
    # Find the column ending with "...Bytes"
    mb_col = [col for col, data in enumerate(udp_tokens)
              if data.endswith('Bytes')]

    if len(mb_col) > 0 and len(udp_tokens) >= mb_col[0] + 9:
        # Make a sublist starting after the column named "MBytes"
        stat_tokens = udp_tokens[mb_col[0]+1:]
        # Rebuild Mbits/sec out of Mbits sec
        multiplier = '%s/%s' % tuple(stat_tokens[1:3])
        return {prefix + 'throughput':
                    apply_multiplier(stat_tokens[0], multiplier),
                prefix + 'jitter':float(stat_tokens[3]),
                prefix + 'lost':float(stat_tokens[7].strip('()%'))}
    else:
        raise Error('Could not parse UDP line: %s' % line)


def _parse_udp_output(lines):
    """Parses iperf output, returns throughput, jitter, and loss.
------------------------------------------------------------
Client connecting to 172.31.206.152, UDP port 5001
Sending 1470 byte datagrams
UDP buffer size:   110 KByte (default)
------------------------------------------------------------
[  3] local 172.31.206.145 port 39460 connected with 172.31.206.152 port 5001
[ ID] Interval       Transfer     Bandwidth
[  3]  0.0- 3.0 sec    386 KBytes  1.05 Mbits/sec
[  3] Sent 269 datagrams
[  3] Server Report:
[ ID] Interval       Transfer     Bandwidth       Jitter   Lost/Total Datagrams
[  3]  0.0- 3.0 sec    386 KBytes  1.05 Mbits/sec  0.010 ms    1/  270 (0.37%)
------------------------------------------------------------
Server listening on UDP port 5001
Receiving 1470 byte datagrams
UDP buffer size:   110 KByte (default)
------------------------------------------------------------
[  3] local 172.31.206.145 port 5001 connected with 172.31.206.152 port 57416
[ ID] Interval       Transfer     Bandwidth       Jitter   Lost/Total Datagrams
[  3]  0.0- 3.0 sec    386 KBytes  1.05 Mbits/sec  0.085 ms    1/  270 (0.37%)
"""
    byte_lines = [line for line in lines
                  if 'Bytes' in line]
    if len(byte_lines) < 2 or len(byte_lines) > 3:
        raise Error('Wrong number of byte report lines: %d' % len(byte_lines))

    out = _parse_one_udp_line(byte_lines[1], 'uplink_')
    if len(byte_lines) > 2:
        out.update(_parse_one_udp_line(byte_lines[2], 'downlink_'))

    return out


def parse_iperf_output(input):
    if not isinstance(input, list):
        lines = input.decode().split('\n')
        all_text = input.decode()
    else:
        lines = input
        all_text = '\n'.join(lines)

    if 'WARNING' in all_text:
        raise Error('Iperf results contained a WARNING: %s' % all_text)

    if 'Connection refused' in all_text:
        raise Error('Could not connect to iperf server')

    if 'TCP' in lines[1]:
        protocol = 'TCP'
    elif 'UDP' in lines[1]:
        protocol = 'UDP'
    else:
        raise Error('Could not parse header line %s' % lines[1])

    if protocol == 'TCP':
        return _parse_tcp_output(lines)
    elif protocol == 'UDP':
        return _parse_udp_output(lines)
    else:
        raise Error('Unhandled protocol %s' % lines)


def run_client(srv_params, packet_size, sessions, params):
    srv_addr = srv_params.get("ip")
    duration = params.get("duration", 60)

    cmd = "iperf"
    cmd += " -c" + str(srv_addr)
    cmd += " -t" + str(duration)
    cmd += " -P" + str(sessions)
    cmd += " -l" + str(packet_size)

    proc = subprocess.Popen(cmd.split(), stdout = subprocess.PIPE)
    out, err = proc.communicate()

    return parse_iperf_output(out)


def test_bandwidth(srv_params, params):
    packet_sizes = params.get("packet_sizes", 4096)
    sessions = params.get("sessions", 1)

    results = {}
    for sess in sessions:
        result = {}
        for size in packet_sizes:
            values = run_client(srv_params, size, sess, params)
            result[size] = values.get("uplink_throughput")

        results[sess] = result

    return results
