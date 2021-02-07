from collections import OrderedDict
import pandas as pd
from pathlib import Path

from sonar_src.sonar_object import SonarObject
from sonar_src.utils import process_datetime, get_proper_file_name

SONAR_ANALYSES_DTYPE = OrderedDict({
        "organization": "object",
        "project": "object",
        "analysis_key": "object",
        "date": "object",
        "project_version": "object",
        "revision": "object"
})

class Analyses(SonarObject):

    def __init__(self, server, organization, output_path, project_key):
        SonarObject.__init__(
            self,
            endpoint = server + "api/project_analyses/search",
            params =    {
                'p': 1,     # page/iteration
                'ps': 100,  # pageSize
                'project': project_key,
                'from' : None,
            },
            output_path = output_path
        )

        self.__organization = organization
        self.__project_key = project_key
        self.__analysis_keys = []           # to return, different from element_list
        self.__analysis_dates = []          # to return, different from element_list
        self.__latest_ts = None
        self.__file_name = get_proper_file_name(self.__project_key)

    def __get_last_analysis_ts_on_file(self):

        output_path = Path(self._output_path).joinpath("analyses")
        if not output_path.exists():
            return None

        archive_file_path = output_path.joinpath(f"{self.__file_name}.csv")
        if not archive_file_path.exists():
                return None
        try:
            analyses_df = pd.read_csv(archive_file_path.absolute(), dtype=SONAR_ANALYSES_DTYPE, parse_dates=['date'])
            last_analysis_ts = analyses_df['date'].max()

            return last_analysis_ts
        except Exception as e:
            print(f"Exception {e} reading latest analysis timestamp from file {archive_file_path}")
            return None

    def _write_csv(self):
        analysis_list = []
        last_analysis_ts = self.__get_last_analysis_ts_on_file()
        for analysis in self._element_list:

            analysis_key = None if 'key' not in analysis else analysis['key']
            date = None if 'date' not in analysis else process_datetime(analysis['date'])
            if date is not None and last_analysis_ts is not None and date <= last_analysis_ts:
                continue
            project_version = None if 'projectVersion' not in analysis else analysis['projectVersion']
            revision = None if 'revision' not in analysis else analysis['revision']
            line = (self.__organization, self.__project_key, analysis_key, date, project_version, revision)
            analysis_list.append(line)

        if analysis_list:

            output_path = Path(self._output_path).joinpath("analyses")
            output_path.mkdir(parents=True, exist_ok=True)

            file_path = output_path.joinpath(f"{self.__file_name}_staging.csv")

            df = pd.DataFrame(data=analysis_list, columns=list(SONAR_ANALYSES_DTYPE.keys()))
            df.to_csv(file_path, index=False, header=True, mode='w')
            self.__analysis_keys = df['analysis_key'].values.tolist()
            self.__analysis_dates = df['date'].values

    # Try to read latest timestamp recorded to get only later analyses
    def __prepare_anlysis_query(self):
        output_path = Path(self._output_path).joinpath("analyses")
        output_path.mkdir(parents=True, exist_ok=True)
            
        archive_file = output_path.joinpath(f"{self.__file_name}.csv")

        latest_ts = None
        if archive_file.exists():
            try:
                old_df = pd.read_csv(archive_file.absolute(), dtype=SONAR_ANALYSES_DTYPE, parse_dates=['date'])
                latest_ts = old_df['date'].max()
                latest_ts_str = latest_ts.strftime(format = '%Y-%m-%d')
                self._params['from'] = latest_ts.strftime(format = latest_ts_str)

            except Exception as e:
                print(f"\t\tERROR: {e} when parsing {archive_file} into DataFrame.")
        
    def process_elements(self):
        self.__prepare_anlysis_query()
        self._query_server(key = 'analyses')
        self._write_csv()

    def get_analysis_keys_dates(self):
        return (self.__analysis_keys, self.__analysis_dates)
