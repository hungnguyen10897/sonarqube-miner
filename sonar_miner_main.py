import argparse
from sonar_project import Projects
from sonar_metric import Metrics
from sonar_analysis import Analysis
from sonar_measure import Measures
from sonar_issue import Issues

COURSE_SERVER = "https://course-sonar.rd.tuni.fi/"
SONAR63 = "http://sonar63.rd.tut.fi/"
SONARCLOUD = "https://sonarcloud.io/"
SERVER = SONARCLOUD

def fetch_sonar_data(output_path, server, organization):

    print(f"Fetching data from server {server} - organization {organization}")

    metrics = Metrics(server, output_path)
    metrics.process_elements()
    server_metrics = metrics.get_server_metrics()

    prj = Projects(server, organization, output_path)
    projects = prj.process_elements()
    projects.sort(key=lambda x: x['key'])

    print(f"Total {len(projects)} projects.")
    i = 0
    for project in projects:
        print(f'{i}. {project["name"]}:')
        i += 1
        analysis = Analysis(server, output_path, project['key'])
        analysis.process_elements()
        analysis_keys_dates = analysis.get_analysis_keys_dates()    # (keys, dates) tuple 

        if len(analysis_keys_dates[0]) == 0:
            continue
        print(f"\t{len(analysis_keys_dates[0])} new analyses")

        measure = Measures(server, output_path, project['key'], analysis_keys_dates, server_metrics)
        measure.process_elements()

        issues = Issues(server, output_path, project['key'], analysis_keys_dates)
        issues.process_elements()
        
if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--output-path", default='./sonar_data', help="Path to output file directory.")
    ap.add_argument("-s", "--server", default=SERVER, help="Sonarqube Server.")
    ap.add_argument("-o", "--organization", default="", help="Sonarqube organization.")
    args = vars(ap.parse_args())

    output_path = args['output_path']
    server = args['server']
    organization = args['organization']
    if organization == "":
        organization = "default-organization" if server != SONARCLOUD else "apache"

    fetch_sonar_data(output_path, server, organization)
