import sys
import os
import argparse
import yaml
import collections
import csv
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

    parser.add_argument("-r", "--result", metavar='OUTPUT',
        dest="result_dir", required=True, help="Path to result directory")

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

def dump_results(funcname, results, dir):
    for sess in results:
        print("sess: " + str(sess))
        filename = funcname + "_sessions_" + str(sess)
        path = os.path.join(dir, filename)

        with open(path, "w") as outfile:
            csvwriter = csv.writer(outfile)
            csvwriter.writerow(dict(results[sess]))
            csvwriter.writerow(dict(results[sess]).values())

def run_tests(result_dir, srv_params, tests):
    for test in tests:
        funcname = list(test.keys())[0]
        params = list(test.values())[0]

        results = test_funcs[funcname](srv_params, params)
        results = collections.OrderedDict(sorted(results.items()))
        print(funcname + " = ", results)

        dump_results(funcname, results, result_dir)

def create_result_dir(path):
    os.makedirs(path, mode=0o777)

def Main(argv=sys.argv):
    parser = create_parser()
    args = parser.parse_args(sys.argv[1:])
    data = parse_script(args.script)

    srv_params = get_server_params(data)
    create_result_dir(args.result_dir)
    run_tests(args.result_dir, srv_params, data['tests'])
