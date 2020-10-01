from collections import OrderedDict
import pandas as pd
import os, sys, csv
from datetime import datetime
from pathlib import Path
from sonar_object import SonarObject
from route_config import RequestsConfig
from utils import get_proper_file_name

def safe_cast(val, to_type, contain_comma=False, list_with_semicolon=False):
    if to_type in ['INT', 'WORK_DUR']:
        try:
            return int(val)
        except (ValueError, TypeError):
            print("WARNING: exception casting value {0} to type {1}".format(str(val), to_type))
            return None
    elif to_type in ['FLOAT', 'PERCENT', 'RATING']:
        try:
            return float(val)
        except (ValueError, TypeError):
            print("WARNING: exception casting value {0} to type {1}".format(str(val), to_type))
            return None
    elif to_type == 'BOOL':
        try:
            return bool(val)
        except (ValueError, TypeError):
            print("WARNING: exception casting value {0} to type {1}".format(str(val), to_type))
            return None
    elif to_type == 'MILLISEC':
        try:
            if len(val) >= 12:
                return datetime.fromtimestamp(int(val) / 1000)
            else:
                return int(val)
        except (ValueError, TypeError):
            print("WARNING: exception casting value {0} to type {1}".format(str(val), to_type))
            return None
    else:
        try:
            value = str(val)
            if contain_comma:
                value = value.replace(',', ';')
            if list_with_semicolon:
                value = value.replace(';', ',')
            return value
        except (ValueError, TypeError):
            print("ERROR: error casting to type {0}".format(to_type))
            return None

def concat_measures(measures_1, measures_2):
    for measure_1, measure_2 in zip(measures_1, measures_2):
        if measure_2['history']:
            measure_1['history'] = measure_1['history'] + measure_2['history']
    return measures_1

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

class Measures(SonarObject):
    def __init__(self, server, output_path, project_key, analysis_keys_dates, server_metrics):
        SonarObject.__init__(
            self,
            endpoint = server + "api/measures/search_history",
            params =    {
                'p': 1,     # page/iteration
                'ps': 1000,  # pageSize
                'component': project_key,
                'from' : None,
            },
            output_path = output_path
        )
        self.__columns = []
        self.__data = {}
        self.__project_key = project_key
        self.__analysis_keys = analysis_keys_dates[0]
        self.__analysis_dates = analysis_keys_dates[1]
        self.__server_metrics = server_metrics
        self.__file_name = get_proper_file_name(self.__project_key)

    def __prepare_measure_query(self):
        if len(self.__analysis_dates) > 0:
            min_ts_str = pd.Timestamp(self.__analysis_dates.min()).to_pydatetime().strftime(format = '%Y-%m-%d')
            self._params['from'] = min_ts_str

    # Different implementation from superclass method at line
    # meansures = concat_meansures(meansires, self._query_server)
    def _query_server(self):
        response_dict = self._call_api()
        if response_dict is None:
            return []
        
        measures = response_dict["measures"]
        self.__total_num_measures = response_dict['paging']['total']

        if self._more_elements():
            self._params['p'] = self._params['p'] + 1
            measures = concat_measures(measures, self._query_server())
        return measures

    def __extract_measures_value(self, measures, metrics_order_type, non_server_metrics):

        num_rows = len(self.__analysis_keys)

        data = OrderedDict()
        data['project_key'] = [self.__project_key] * num_rows
        data['analysis_key'] = self.__analysis_keys

        columns = ['project_key', 'analysis_key']

        for measure in measures:
            metric = measure['metric']
            columns.append(metric)

            # Non-server metric
            if metric in non_server_metrics:
                values = [None] * num_rows
            else:
                history = measure['history']
                metric_type = metrics_order_type[metric][1]

                contain_comma = False
                if metric in ['quality_profiles', 'quality_gate_details']:
                    contain_comma = True

                list_with_semicolon = False
                if metric in ['class_complexity_distribution', 'function_complexity_distribution',
                            'file_complexity_distribution', 'ncloc_language_distribution']:
                    list_with_semicolon = True

                values = list(map(lambda x: None if 'value' not in x else safe_cast(x['value'], metric_type, contain_comma, list_with_semicolon), history))
                values.reverse()            
                values = values[:num_rows]  # get only num_rows latest values

                # Interpolate with None till num_rows
                if len(values) < num_rows:
                    values = values + [None] * (num_rows - len(values))

                if metric_type == "INT":
                    values = pd.array(values, dtype=pd.Int64Dtype())

            data[metric] = values
            
        return columns, data

    def _write_csv(self):
        output_path = Path(self._output_path).joinpath("measures")
        output_path.mkdir(parents=True, exist_ok=True)
        file_path = output_path.joinpath(f"{self.__file_name}_staging.csv")

        df = pd.DataFrame(data=self.__data, columns=self.__columns)
        df.to_csv(file_path, index=False, header=True, mode='w')

    def __metric_wise_search(self):
        all_metrics_order_type = read_all_metrics()
        all_metrics_set = set(all_metrics_order_type.keys())
        non_server_metrics = all_metrics_set.difference(set(self.__server_metrics))

        measures = []

        for i in range(0, len(self.__server_metrics), 10):
            self._params['metrics'] = ','.join(self.__server_metrics[i:i + 10])
            self._params['p'] = 1
            measures = measures + self._query_server()

        # Adding non-server metrics
        for non_server_metric in non_server_metrics:
            measures.append({'metric' : non_server_metric})

        measures.sort(key=lambda x: all_metrics_order_type[x['metric']][0])

        self.__columns, self.__data = self.__extract_measures_value(measures, all_metrics_order_type, non_server_metrics)
        
    def process_elements(self):
        self.__prepare_measure_query()
        self.__metric_wise_search()
        self._write_csv()
