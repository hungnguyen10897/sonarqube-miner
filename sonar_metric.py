import pandas as pd
from pathlib import Path
from sonar_object import SonarObject
from route_config import RequestsConfig
from collections import OrderedDict

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

        self.__sonar_metrics_dtype = OrderedDict({
            'project': 'object',
            'analysis_key': 'object',
        })

    def _write_csv(self):
        metrics = []
        self._element_list.sort(key=lambda x: ('None' if 'domain' not in x else x['domain'], int(x['id'])))
        for metric in self._element_list:
            if metric == 'sonarjava_feedback':
                continue
            self.__sonar_metrics_dtype[metric['key']] = TYPE_CONVERSION[metric['type']]
            metric = ('No Domain' if 'domain' not in metric else metric['domain'],
                      'No Key' if 'key' not in metric else metric['key'],
                      'No Type' if 'type' not in metric else metric['type'],
                      'No Description' if 'description' not in metric else metric['description'])

            metrics.append(metric)

        if metrics:
            headers = ['domain', 'key', 'type', 'description']
            output_path = Path(self._output_path).joinpath("metrics")
            output_path.mkdir(parents=True, exist_ok=True)
            file_path = output_path.joinpath("metrics.csv")
            df = pd.DataFrame(data=metrics, columns=headers)
            df.to_csv(file_path, index=False, header=True)

    def process_elements(self):
        self._query_server(key = "metrics")
        self._write_csv()
        return self.__sonar_metrics_dtype
