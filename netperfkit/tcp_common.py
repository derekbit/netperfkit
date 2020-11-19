import subprocess

class Error(Exception):
    pass

def _parse_one_line(testname, line):
    tokens = line.split()

    if testname == 'tcp_stream' and len(tokens) == 5:
        return (float(tokens[-1]) * 1.0e3)
    elif (testname == 'tcp_rr' or testname == 'tcp_crr') and len(tokens) == 6:
        return float(tokens[-1])
    else:
        raise Error('Could not parse line')

def parse_netperf_output(testname, input):
    """Parses the following and returns the Trans. Rate per sec (126220.01).
    16384  87380  1        1       1.00     126220.01   
    16384  87380 
    """
    if not isinstance(input, list):
        lines = input.decode().split('\n')
        all_text = input
    else:
        lines = input
        all_text = '\n'.join(lines)

    return _parse_one_line(testname, lines[0])

def run_client(testname, srv_params, packet_size, sessions, params, create_cmd):
    cmd = create_cmd(srv_params, packet_size, params)

    proc = [None] * sessions
    for i in range(sessions):
        proc[i] = subprocess.Popen(cmd.split(), stdout = subprocess.PIPE)

    total = 0.0
    for i in range(sessions):
        out, err = proc[i].communicate()
        total += parse_netperf_output(testname, out)

    return total

def test_tcp(testname, srv_params, params, create_cmd):
    packet_sizes = params.get("packet_sizes", 4096)
    sessions = params.get("sessions", 1)

    results = {}
    for sess in sessions:
        result = {}
        for size in packet_sizes:
            result[size] = run_client(testname, srv_params, size, sess, params, create_cmd)

        results[sess] = result

    return results
