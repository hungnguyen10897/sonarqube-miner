from datetime import datetime, timedelta
import sys

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