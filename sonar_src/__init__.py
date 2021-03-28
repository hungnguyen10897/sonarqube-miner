from sonar_src.sonar_project import Projects
from sonar_src.sonar_metric import Metrics
from sonar_src.sonar_analysis import Analyses
from sonar_src.sonar_measure import Measures
from sonar_src.sonar_issue import Issues
from sonar_src.sonar_rule import Rules
from sonar_src.sonar_component_project import ComponentProject
from sonar_src.sonar_file import Files

import sys

def fetch_organization_sonar_data(output_path, organization = 'apache', server = "https://sonarcloud.io/", component_wise=False):

    print(f"Fetching data from server {server} - organization {organization}")

    metrics = Metrics(server, output_path)
    metrics.process_elements()
    server_metrics = metrics.get_server_metrics()

    r = Rules(server, organization)
    rules = r.get_server_rules()

    prj = Projects(server, organization, output_path)
    projects = prj.process_elements()
    projects.sort(key=lambda x: x['key'])

    print(f"Total {len(projects)} projects.")
    i = 0
    for project in projects:
        print(f'{i}. {project["name"]}:')
        i += 1
        analysis = Analyses(server, organization, output_path, project['key'])
        analysis.process_elements()
        analysis_keys_dates = analysis.get_analysis_keys_dates()    # (keys, dates) tuple 

        if len(analysis_keys_dates[0]) == 0:
            continue
        print(f"\t{len(analysis_keys_dates[0])} new analyses")

        measure = Measures(server, organization, output_path, project['key'], project['key'], project['key'], analysis_keys_dates, server_metrics)
        measure.process_elements()

        issues = Issues(server, organization, output_path, project['key'], project['key'], project['key'], analysis_keys_dates, rules)
        issues.process_elements()

        if not component_wise:
            continue

        files = Files(server, project['key']).get_files()
        for file in files:
            file_key = file[0]
            file_name = file[1]
            
            print(f"\t{file_name} - {file_key}")

            # Measures are the same for all files
            
            # measure = Measures(server, organization, output_path, project['key'], file_key, file_name, analysis_keys_dates, server_metrics)
            # measure.process_elements()

            issues = Issues(server, organization, output_path, project['key'], file_key, file_name, analysis_keys_dates, rules)
            issues.process_elements()

def fetch_projects_sonar_data(output_path, server, projects, component_wise=False):

    print(f"Fetching data from server {server} - project {projects}")

    metrics = Metrics(server, output_path)
    metrics.process_elements()
    server_metrics = metrics.get_server_metrics()

    print(f"Total {len(projects)} projects.")
    i = 0
    for project in projects:

        print(f'{i}. {project}:')
        i += 1
        
        organization = ComponentProject(server, project).get_organization()
        if organization is None:
            print(f"ERROR: Cannot find project {project} on server {server}")
            sys.exit(1)

        r = Rules(server, organization)
        rules = r.get_server_rules()

        analysis = Analyses(server, organization, output_path, project)
        analysis.process_elements()
        analysis_keys_dates = analysis.get_analysis_keys_dates()    # (keys, dates) tuple 

        if len(analysis_keys_dates[0]) == 0:
            continue
        print(f"\t{len(analysis_keys_dates[0])} new analyses")

        measure = Measures(server, organization, output_path, project, project, project, analysis_keys_dates, server_metrics)
        measure.process_elements()

        issues = Issues(server, organization, output_path, project, project, project, analysis_keys_dates, rules)
        issues.process_elements()

        if not component_wise:
            continue

        files = Files(server, project).get_files()
        for file in files:
            file_key = file[0]
            file_name = file[1]
            
            print(f"\t{file_name} - {file_key}")

            # Measures are the same for all files
            
            # measure = Measures(server, organization, output_path, project, file_key, file_name, analysis_keys_dates, server_metrics)
            # measure.process_elements()

            issues = Issues(server, organization, output_path, project, file_key, file_name, analysis_keys_dates, rules)
            issues.process_elements()