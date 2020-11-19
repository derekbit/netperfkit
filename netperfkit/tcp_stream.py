import subprocess
from netperfkit.tcp_common import parse_netperf_output, run_client, test_tcp

def create_cmd(srv_params, packet_size, params):
    srv_addr = srv_params.get("ip")
    duration = params.get("duration", 10)
    parallel = params.get("parallel", 1)

    cmd = "netperf"
    cmd += " -H" + str(srv_addr)
    cmd += " -l" + str(duration)
    cmd += " -ttcp_stream"
    cmd += " -P0"
    cmd += " -fK"
    cmd += " --"
    cmd += " -m" + str(packet_size)
    cmd += " &"

    return cmd

def test_tcp_stream(srv_params, params):
    return test_tcp("tcp_stream", srv_params, params, create_cmd)
