from sonar_src.sonar_project import Projects
from sonar_src.sonar_metric import Metrics
from sonar_src.sonar_analysis import Analyses
from sonar_src.sonar_measure import Measures
from sonar_src.sonar_issue import Issues
from sonar_src.sonar_rule import Rules

def fetch_sonar_data(output_path, organization = 'apache', server = "https://sonarcloud.io/"):

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

        measure = Measures(server, organization, output_path, project['key'], analysis_keys_dates, server_metrics)
        measure.process_elements()

        issues = Issues(server, organization, output_path, project['key'], analysis_keys_dates, rules)
        issues.process_elements()