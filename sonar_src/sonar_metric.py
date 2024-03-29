import pandas as pd
from pathlib import Path
from collections import OrderedDict

from .sonar_object import SonarObject
from .route_config import RequestsConfig
from .utils import read_used_metrics

TYPE_CONVERSION = {
    "INT": "Int64",
    "FLOAT": 'float64',
    "DISTRIB": 'object',
    "PERCENT": 'float64',
    "MILLISEC": 'float64',
    "DATA": 'object',
    "BOOL": 'bool',
    "STRING": 'object',
    "WORK_DUR": 'float64',
    "RATING": 'float64',
    "LEVEL": 'float64'
}

class Metrics(SonarObject):

    def __init__(self, server, output_path):
        SonarObject.__init__(
            self,
            endpoint = server + "api/metrics/search",
            params =    {
                'p': 1,     # page/iteration
                'ps': 100,  # pageSize
            },
            output_path = output_path
        )
        self.__server_metrics = []

    def _write_csv(self):

        metrics = []
        self._element_list.sort(key=lambda x: ('None' if 'domain' not in x else x['domain'], x['id']))

        all_metrics_order_type = read_used_metrics()
        all_metrics_set = set(all_metrics_order_type.keys())
        has_new_metric = False

        for element in self._element_list:

            # Ignore this, extremely long
            if element['key'] == 'sonarjava_feedback':
                continue

            metric = (  
                        element['id'],
                        'No Domain' if 'domain' not in element else element['domain'],
                        'No Key' if 'key' not in element else element['key'],
                        'No Type' if 'type' not in element else element['type'],
                        'No Description' if 'description' not in element else element['description']
                    )
            metrics.append(metric)
            self.__server_metrics.append(element['key'])

            # New metric
            if element['key'] not in all_metrics_set:
                if not has_new_metric:
                    print(f"WARNING: There are new metrics from the server. Please update to include those metrics:")
                    has_new_metric = True
                print(f"\t{' - '.join(metric)}")

        if metrics:
            output_path = Path(self._output_path).joinpath("metrics")
            output_path.mkdir(parents=True, exist_ok=True)
            file_path = output_path.joinpath("metrics.txt")
            with open(file_path, 'w') as f:
                for metric in metrics:
                    f.write(" - ".join(metric)+"\n")

    def process_elements(self):
        self._query_server(key = "metrics")
        self._write_csv()

    def get_server_metrics(self):
        return self.__server_metrics
