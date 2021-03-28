import pandas as pd
from collections import OrderedDict
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import sys

from sonar_src.utils import process_datetime, get_duration_from_str, get_proper_file_name
from sonar_src.sonar_object import SonarObject
from sonar_src.route_config import RequestsConfig

ISSUES_PAGE_SIZE = 500

SONAR_ISSUES_TYPE = OrderedDict({
    "organization": "object",
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
    def __init__(self, server, organization, output_path, project_key, component_key, component_name, analysis_keys_dates, rules):
        SonarObject.__init__(
            self,
            endpoint = server + "api/issues/search",
            params = {
                'p': 1,                         # varialbe
                'ps': ISSUES_PAGE_SIZE,
                'componentKeys': component_key,
            },
            output_path = output_path
        )

        self.__organizaiton = organization
        self.__project_key = project_key
        self.__component_key = component_key
        # dates are in decreasing order
        self.__analysis_keys_dates = list(zip(analysis_keys_dates[0], analysis_keys_dates[1]))
        self._element_list = []
        self.__file_name = get_proper_file_name(component_name)
        self.__rules = rules

    def _more_elements(self, issues_num):
        max_issues_num = issues_num if issues_num <= 10000 else 10000
        if self._params['p'] * self._params['ps'] < max_issues_num:
            return True
        return False

    def _sub_query_server(self):
        response_dict = self._call_api()
        if response_dict is None:
            return []

        issues = response_dict["issues"]
        issues_num = response_dict['total']
        
        if self._more_elements(issues_num):
            self._params['p'] += 1
            issues += self._sub_query_server()

        return issues

    def _query_server(self):

        # First api call to check total number of issues
        self._params["ps"] = 1  # Reduce data to load
        response_dict = self._call_api()
        if response_dict is None:
            return
        total_issues = response_dict['total']

        if total_issues > 10000:
            
            for severity in ["INFO", "MINOR", "MAJOR", "CRITICAL", "BLOCKER"]:
                
                self._params['severities'] = severity
                self._params["ps"] = 1
                response_dict = self._call_api()
                if response_dict is None:
                    return
                severity_total_issues = response_dict['total']
                self._params["ps"] = ISSUES_PAGE_SIZE

                # Still >10000 issues for the severity,
                # iterate by rules,
                if severity_total_issues > 10000:
                    for rule in self.__rules:
                        self._params['rules'] = rule
                        self._element_list += self._sub_query_server()
                        self._params['p'] = 1
                        self._params['rules'] = None
                else:
                    self._element_list += self._sub_query_server()
                self._params['p'] = 1
                self._params['severities'] = None

        else:
            self._params["ps"] = ISSUES_PAGE_SIZE
            self._element_list += self._sub_query_server()

    def __get_old_issues_df(self):

        # Condition: query issues data for component file in the project
        if self.__project_key != self.__component_key:
            issues_archive_file_path = Path(self._output_path).joinpath("issues").joinpath(get_proper_file_name(self.__project_key)).joinpath(f"{self.__file_name}.csv") 
        else:
            issues_archive_file_path = Path(self._output_path).joinpath("issues").joinpath(f"{self.__file_name}.csv") 

        if not issues_archive_file_path.exists():
            return None
        
        try:
            old_issues_df = pd.read_csv(issues_archive_file_path.absolute(), dtype=SONAR_ISSUES_TYPE, parse_dates=["creation_date", "update_date", "close_date"])
            return old_issues_df

        except Exception as e:
            print(f"Exception {e} reading latest analysis timestamp from file {issues_archive_file_path.absolute()}")
            return None

    def _write_csv(self):

        if not self._element_list:
            print("\tNo issues queried.")
            return

        # Condition: query issues data for component file in the project
        if self.__project_key != self.__component_key:
            output_path = Path(self._output_path).joinpath("issues").joinpath(get_proper_file_name(self.__project_key))
        else:
            output_path = Path(self._output_path).joinpath("issues")

        output_path.mkdir(parents=True, exist_ok=True)
        
        file_path = output_path.joinpath(f"{self.__file_name}_staging.csv")
    
        issues = []

        for project_issue in self._element_list:

            update_date = None if 'updateDate' not in project_issue else process_datetime(project_issue['updateDate'])
            current_analysis_key = None if update_date is None else get_analysis_key(update_date, self.__analysis_keys_dates)

            issue_key = None if 'key' not in project_issue else project_issue['key']
            creation_date = None if 'creationDate' not in project_issue else process_datetime(
                project_issue['creationDate'])
            creation_analysis_key = None if creation_date is None else get_analysis_key(creation_date, self.__analysis_keys_dates)

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
            from_hotspot = None if 'fromHotspot' not in project_issue else str(project_issue['fromHotspot'])

            issue = (self.__organizaiton, self.__project_key, current_analysis_key, creation_analysis_key, issue_key, issue_type, rule,
                        severity, status, resolution, effort, debt, tags, creation_date, update_date, close_date, message,
                        component, start_line, end_line, start_offset, end_offset, hash_value, from_hotspot)
            issues.append(issue)

        issues_df = pd.DataFrame(data=issues, columns=SONAR_ISSUES_TYPE.keys())
        issues_df = issues_df.astype({
            "effort": "Int64",
            "debt": "Int64",
            "start_line" : "Int64",
            "end_line" : "Int64",
            "start_offset" : "Int64",
            "end_offset" : "Int64",
            "creation_date" : "datetime64[ns]",
            "update_date" : "datetime64[ns]",
            "close_date" : "datetime64[ns]",
        })
        old_issues_df = self.__get_old_issues_df()
        if old_issues_df is not None:
            new_issues_df = issues_df.merge(old_issues_df, how = 'outer' ,indicator=True).loc[lambda x : x['_merge']=='left_only'].drop(['_merge'], axis=1)
        else:
            new_issues_df = issues_df
            
        print(f"\t{new_issues_df.shape[0]} new issues")
        new_issues_df.to_csv(file_path, index=False, header=True, mode='w')

    def process_elements(self):
        self._query_server()
        self._write_csv()
