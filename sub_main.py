import argparse
from sonar_project import Projects
from sonar_metric import Metrics
from sonar_analysis import Analysis
from sonar_measure import Measures
# from sonar_issue import Issues

COURSE_SERVER = "https://course-sonar.rd.tuni.fi/"
SONAR63 = "http://sonar63.rd.tut.fi/"
server = SONAR63

ORGANIZATION = "default-organization"

def fetch_sonar_data(output_path):
    # Run only once
    metrics = Metrics(server, output_path)
    metrics.process_elements()

    prj = Projects(server, ORGANIZATION, output_path)
    projects = prj.process_elements()
    projects.sort(key=lambda x: x['key'])

    print("Total: {0} projects.".format(len(projects)))
    for project in projects[:10]:
        # print(f'{project["name"]} ', end = "")
        analysis = Analysis(server, output_path, project['key'])
        analysis.process_elements()
        analysis_keys = analysis.get_analysis_keys()

        if len(analysis_keys) == 0:
            continue

        print(f"{len(analysis_keys)} analyses.")

        measure = Measures(SONAR63, project_key=project['key'], output_path=output_path,  analysis_keys=analysis_keys)
        measure.process_elements()

        
if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output-path", default='./sonar_data', help="Path to output file directory.")
    args = vars(ap.parse_args())
    output_path = args['output_path']
    fetch_sonar_data(output_path)
    print("Finish")
