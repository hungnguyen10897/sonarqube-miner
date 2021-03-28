import pandas as pd
from pathlib import Path

from sonar_src.sonar_object import SonarObject
from sonar_src.route_config import RequestsConfig

class Files(SonarObject):
    def __init__(self, server, project_key):
        SonarObject.__init__(
            self,
            endpoint = server + "api/components/tree",
            params = {
                'p': 1,     # page/iteration
                'ps': 100,  # pageSize
                'component' : project_key,
                'qualifiers': 'FIL'
            },
            output_path = None
        )

    def get_files(self):
        self._query_server(key = "components")

        file_keys = []
        file_names = []
        name_records = {} # In case of duplicate file names

        for e in self._element_list:
            file_keys.append(e["key"])

            name = e["name"]
            if name not in name_records:
                file_names.append(name)
                name_records[name] = 1
            else:
                name_records[name] = name_records[name] + 1
                file_names.append(name + f"_{name_records[name]}")

        return list(zip(file_keys, file_names))