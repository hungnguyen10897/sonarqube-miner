import argparse
from sonar_project import Projects
from sonar_metric import Metrics
from sonar_analysis import Analysis
# from sonar_measure import Measures
# from sonar_issue import Issues

COURSE_SERVER = "https://course-sonar.rd.tuni.fi/"
SONAR63 = "http://sonar63.rd.tut.fi/"
server = SONAR63

ORGANIZATION = "default-organization"

def fetch_sonar_data(output_path):
    metrics = Metrics(server, output_path)
    metrics_list = metrics.process_elements()
    for key,val in metrics_list.items():
        print(f"{key} - {val}")

    prj = Projects(server, ORGANIZATION, output_path)
    projects = prj.process_elements()
    projects.sort(key=lambda x: x['key'])

    print("Total: {0} projects.".format(len(projects)))
    for project in projects:
        #print('{0} starts'.format(project['name']))
        analysis = Analysis(server, output_path, project['key'])
        analyses = analysis.get_analyses()
        #print('{0} analysis completed'.format(project['name']))

        if analyses is None:
            continue
        
        for a in analyses:
            print(a)
        
if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output-path", default='./sonar_data', help="Path to output file directory.")
    args = vars(ap.parse_args())
    output_path = args['output_path']
    fetch_sonar_data(output_path)
    print("Finish")
