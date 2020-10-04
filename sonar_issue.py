import pandas as pd
from collections import OrderedDict
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import sys
from sonar_object import SonarObject
from route_config import RequestsConfig
from utils import process_datetime, get_duration_from_str, get_proper_file_name
from sonar_analysis import SONAR_ANALYSES_DTYPE

SONAR_ISSUES_TYPE = OrderedDict({
    "project": "object",
    "current_analysis_key": "object",
    "creation_analysis_key": "object",
    "issue_key": "object",
    "type": "object",
    "rule": "object",
    "severity": "object",
    "status": "object",
    "resolution": "object",
    "effort": "Int64",
    "debt": "Int64",
    "tags": "object",
    "creation_date": "object",
    "update_date": "object",
    "close_date": "object",
    # Additional fields
    "message": "object",
    "component": "object",
    "start_line": "Int64",
    "end_line": "Int64",
    "start_offset": "Int64",
    "end_offset": "Int64",
    "hash": "object",
    "from_hotspot": "object"
})

def get_analysis_key(date, key_date_list):

    date = np.datetime64(date)
    for i in range(len(key_date_list)):
        analysis_date = key_date_list[i][1]
        if date >= analysis_date:
            return key_date_list[i][0]
    return key_date_list[-1][0]

def get_creation_analysis_key(issue_key, creation_date, issue_key_analysis_map, key_date_list):
    if issue_key not in issue_key_analysis_map:
        return get_analysis_key(creation_date, key_date_list)
    return issue_key_analysis_map[issue_key]

class Issues(SonarObject):
    def __init__(self, server, output_path, project_key, analysis_keys_dates):
        SonarObject.__init__(
            self,
            endpoint = server + "api/issues/search",
            params = {
                'p': 1,                         # varialbe
                'ps': 500,
                'componentKeys': project_key,
                'createdAfter': None,           # variable
                'createdBefore' : None,         # variable
                's': 'CREATION_DATE'
            },
            output_path = output_path
        )

        self.__project_key = project_key
        # dates are in decreasing order
        self.__analysis_keys_dates = list(zip(analysis_keys_dates[0], analysis_keys_dates[1]))
        self._element_list = []
        self.__file_name = get_proper_file_name(self.__project_key)

    def __get_last_analysis_ts_on_file(self):

        output_path = Path(self._output_path).joinpath("analysis")
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

    def _more_elements(self, partial_issues_num):
        if self._params['p'] * self._params['ps'] < partial_issues_num:
            return True
        return False

    def _sub_query_server(self):
        response_dict = self._call_api()
        if response_dict is None:
            return []

        issues = response_dict["issues"]
        partial_issues_num = response_dict['paging']['total']
        
        # > 10 000 issues for current createdBefore, createdAfter parameters
        if partial_issues_num > 10000:
            return None

        if self._more_elements(partial_issues_num):
            self._params['p'] += 1
            issues += self._sub_query_server()

        return issues

    def _query_server(self):

        # This means at the one timestamp there are > 10 000 issues
        if self._params['createdAfter'] is not None and self._params['createdBefore'] is not None and self._params['createdBefore'] < self._params['createdAfter']:
            timestamp = self._params['createdAfter']
            self._params['createdAt'] = timestamp  
            self._params['createdAfter'] = None
            self._params['createdBefore'] = None
            for severity in ["INFO", "MINOR", "MAJOR", "CRITICAL", "BLOCKER"]:
                self._params['severities'] = severity
                self._element_list += self._sub_query_server()
                self._params['p'] = 1
                self._params['severities'] = None
            self._params['createdAt'] = None

            next_timestamp = datetime.strptime(timestamp[:19], "%Y-%m-%dT%H:%M:%S") + timedelta(seconds=1)

            next_timestamp = '{0}-{1}-{2}T{3}:{4}:{5}{6}'.format(next_timestamp.strftime('%Y'), next_timestamp.strftime('%m'),
                                                                next_timestamp.strftime('%d'), next_timestamp.strftime('%H'),
                                                                next_timestamp.strftime('%M'), next_timestamp.strftime('%S'),
                                                                timestamp[19:])
            self._params['createdAfter'] = next_timestamp
            self._params['createdBefore'] = None

        # First api call to check total number of issues
        response_dict = self._call_api()
        if response_dict is None:
            return

        total_issues = response_dict['paging']['total']
        if total_issues > 10000:
            # Go to last 'page' to check timestamp, returned is sorted time wise
            self._params['p'] = 20
            response_dict = self._call_api()
            if response_dict is None:
                return

            last_timestamp = response_dict['issues'][-1]['creationDate']
            previous_timestamp = datetime.strptime(last_timestamp[:19], "%Y-%m-%dT%H:%M:%S") + timedelta(seconds=-1)

            previous_timestamp = '{0}-{1}-{2}T{3}:{4}:{5}{6}'.format(previous_timestamp.strftime('%Y'), previous_timestamp.strftime('%m'),
                                                                previous_timestamp.strftime('%d'), previous_timestamp.strftime('%H'),
                                                                previous_timestamp.strftime('%M'), previous_timestamp.strftime('%S'),
                                                                last_timestamp[19:])

            self._params['p'] = 1
            self._params['createdBefore'] = previous_timestamp
            
            sub_query_result = self._sub_query_server()

            if type(sub_query_result) == list:
                self._element_list += sub_query_result

            # sub_query_result is None
            # meaning that the current createdAfter and createdBefore params still return > 10 000 issues
            # start sub query with 'severities' parameter
            else:   
                for severity in ["INFO", "MINOR", "MAJOR", "CRITICAL", "BLOCKER"]:
                    self._params['severities'] = severity
                    self._element_list += self._sub_query_server()
                    self._params['p'] = 1

            # Prepare for next batch
            self._params['p'] = 1
            self._params['createdAfter'] = last_timestamp
            self._query_server()
    
        else:
            # Last execution
            self._element_list += self._sub_query_server()

    def _write_csv(self):

        if not self._element_list:
            return

        issues = []
        output_path = Path(self._output_path).joinpath("issues")
        output_path.mkdir(parents=True, exist_ok=True)

        latest_analysis_ts_on_file = self.__get_last_analysis_ts_on_file()
        
        file_path = output_path.joinpath(f"{self.__file_name}_staging.csv")

        for project_issue in self._element_list:

            update_date = None if 'updateDate' not in project_issue else process_datetime(project_issue['updateDate'])

            # belong to the analyses on file
            if update_date is not None and latest_analysis_ts_on_file is not None and update_date <= latest_analysis_ts_on_file:
                continue

            current_analysis_key = None if update_date is None else get_analysis_key(update_date, self.__analysis_keys_dates)

            issue_key = None if 'key' not in project_issue else project_issue['key']
            creation_date = None if 'creationDate' not in project_issue else process_datetime(
                project_issue['creationDate'])
            creation_analysis_key = None if creation_date is None else get_analysis_key(creation_date, self.__analysis_keys_dates)
            # Not yet implemented, functionality to fetch only new issues
            # creation_analysis_key = None if creation_date is None else get_creation_analysis_key(issue_key, creation_date, issue_key_analysis_map, key_date_list)

            close_date = None if 'closeDate' not in project_issue else process_datetime(project_issue['closeDate'])
            rule = None if 'rule' not in project_issue else project_issue['rule']
            severity = None if 'severity' not in project_issue else project_issue['severity']
            status = None if 'status' not in project_issue else project_issue['status']
            resolution = None if 'resolution' not in project_issue else project_issue['resolution']
            effort = None if 'effort' not in project_issue else get_duration_from_str(project_issue['effort'])
            debt = None if 'debt' not in project_issue else get_duration_from_str(project_issue['debt'])

            if 'tags' not in project_issue or len(project_issue['tags']) == 0:
                tags = None
            else:
                tags = ','.join(project_issue['tags'])
            issue_type = None if 'type' not in project_issue else project_issue['type']
            message = None if 'message' not in project_issue else project_issue['message']
            component = None if 'component' not in project_issue else project_issue['component']
            start_line = None if 'textRange' not in project_issue else None if 'startLine' not in project_issue[
                'textRange'] \
                else project_issue['textRange']['startLine']
            end_line = None if 'textRange' not in project_issue else None if 'endLine' not in project_issue[
                'textRange'] else project_issue['textRange']['endLine']
            start_offset = None if 'textRange' not in project_issue else None if 'startOffset' not in project_issue[
                'textRange'] else project_issue['textRange']['startOffset']
            end_offset = None if 'textRange' not in project_issue else None if 'endOffset' not in project_issue[
                'textRange'] else project_issue['textRange']['endOffset']
            hash_value = None if 'hash' not in project_issue else project_issue['hash']
            from_hotspot = None if 'fromHotspot' not in project_issue else project_issue['fromHotspot']

            issue = (self.__project_key, current_analysis_key, creation_analysis_key, issue_key, issue_type, rule,
                        severity, status, resolution, effort, debt, tags, creation_date, update_date, close_date, message,
                        component, start_line, end_line, start_offset, end_offset, hash_value, from_hotspot)
            issues.append(issue)

        print(f"\t{len(issues)} new issues")

        df = pd.DataFrame(data=issues, columns=SONAR_ISSUES_TYPE.keys())
        df = df.astype({
            "effort": "Int64",
            "debt": "Int64"
        })
        df.to_csv(file_path, index=False, header=True, mode='w')

    def process_elements(self):
        self._query_server()
        self._write_csv()
