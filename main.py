import argparse
from sonar_src import fetch_sonar_data

COURSE_SERVER = "https://course-sonar.rd.tuni.fi/"
SONAR63 = "http://sonar63.rd.tut.fi/"
SONARCLOUD = "https://sonarcloud.io/"
SERVER = SONARCLOUD

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
