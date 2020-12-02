from datetime import datetime, timedelta
import sys, re, os
from pathlib import Path

def process_datetime(time_str):
    if time_str is None:
        return None

    ts = datetime.strptime(time_str[:19], "%Y-%m-%dT%H:%M:%S")

    offset = timedelta(hours=int(time_str[20:22]), minutes=int(time_str[22:24]))

    if time_str[19] == '-':
        ts = ts + offset
    elif time_str[19] == '+':
        ts = ts - offset

    return ts

def get_duration_from_str(input_str):
    if input_str is not None:
        idx_min = input_str.find('min')
        idx_h = input_str.find('h')
        idx_d = input_str.find('d')

        if idx_d != -1:
            days = int(input_str[:idx_d])
            if len(input_str) == idx_d + 1:
                return 24 * 60 * days
            return 24 * 60 * days + get_duration_from_str(input_str[idx_d + 1:])

        if idx_h != -1:
            hours = int(input_str[:idx_h])
            if len(input_str) == idx_h + 1:
                return 60 * hours
            return 60 * hours + get_duration_from_str(input_str[idx_h + 1:])

        if idx_min != -1:
            minutes = int(input_str[:idx_min])
            return minutes

        print("ERROR: duration string '{0}' does not contain 'min', 'h' or 'd'.".format(input_str))
        sys.exit(1)

def get_proper_file_name(origin):
    p = re.compile("[^0-9a-z-_]")
    return p.sub('_', origin.lower())

def read_all_metrics():

    current_file_path = os.path.realpath(__file__)
    parent_path = '/'.join(current_file_path.split("/")[:-1])
    path = f'{parent_path}/all_metrics.txt'
    p = Path(path)

    if not p.exists():
        print("ERROR: Path for all metrics {0} does not exists.".format(p.resolve()))
        sys.exit(1)
    try:
        metrics_order = {}
        with open(p, 'r') as f:
            order = 0
            for line in f.readlines():
                parts = line.split(" - ")
                metric = parts[2]
                metric_type = parts[3]
                metrics_order[metric] = (order, metric_type)
                order += 1
        return metrics_order
    except Exception as e:
        print("ERROR: Reading metrics file", e)
        sys.exit(1)