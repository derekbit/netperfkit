import sys
import argparse
import yaml
import collections
from netperfkit.tcp_stream import test_tcp_stream
from netperfkit.tcp_rr import test_tcp_rr
from netperfkit.tcp_crr import test_tcp_crr
from netperfkit.bandwidth import test_bandwidth

def parse_script(script):
    with open(script, "r") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)

    return data;

def create_parser():
    parser = argparse.ArgumentParser(description="NetPerfKit")

    parser.add_argument("-s", "--script", metavar='SCRIPT',
        dest="script", required=True, help="Benchmark script")

    return parser

def get_server_params(data):
    srv_params = {
        "ip": data['server']['ip'],
    }

    return srv_params

test_funcs = {
    "tcp_stream": test_tcp_stream,
    "tcp_rr": test_tcp_rr,
    "tcp_crr": test_tcp_crr,
    "bandwidth": test_bandwidth
}

def run_tests(srv_params, tests):
    for test in tests:
        func = list(test.keys())[0]
        params = list(test.values())[0]

        results = test_funcs[func](srv_params, params)
        results = collections.OrderedDict(sorted(results.items()))
        print(func + " = ", results)

def Main(argv=sys.argv):
    parser = create_parser()
    args = parser.parse_args(sys.argv[1:])
    data = parse_script(args.script)

    srv_params = get_server_params(data)
    run_tests(srv_params, data['tests'])
