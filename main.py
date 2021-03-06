import argparse
from sonar_src import fetch_organization_sonar_data, fetch_projects_sonar_data
from pathlib import Path
from urllib.parse import unquote

COURSE_SERVER = "https://course-sonar.rd.tuni.fi/"
SONAR63 = "http://sonar63.rd.tut.fi/"
SONARCLOUD = "https://sonarcloud.io/"
SERVER = SONARCLOUD

def format_server(server):
    if not server.endswith("/"):
        server + "/"
    return server

def get_server_dir_name(server):

    dir_name = ""
    if server.endswith("/"):
        dir_name = server[:-1]

    dir_name = dir_name  \
        .replace("http://", "") \
        .replace("https://", "") \
        .replace("/", "_")

    return dir_name

def iterate_project_file(file):

    server_projects_dict = {}

    f = open(file, 'r')
    for line in f.readlines():
        line = unquote(line)
        server = line.split("dashboard")[0]
        project = line.split("id=")[1].split("&")[0].strip("\n")
        
        projects = set() if server not in server_projects_dict else server_projects_dict[server]
        projects.add(project)

        server_projects_dict[server] = projects
    
    return server_projects_dict

if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--output-path", default='./sonar_data', help="Path to output file directory.")
    ap.add_argument("-s", "--server", default=SERVER, help="Sonarqube Server.")
    ap.add_argument("-o", "--organization", default="", help="Sonarqube organization.")
    ap.add_argument("-f", "--file", help="File containing projects' sonarqube links.")
    ap.add_argument("-c", "--component-wise", default=False, action="store_true", help="Whether to fetch issues data for all components of project.")
    args = vars(ap.parse_args())

    output_path = args['output_path']
    server = format_server(args['server'])
    organization = args['organization']
    component_wise = args['component_wise']

    if args["file"] is not None:
        file = args["file"]
        print(f"Fetching projects' data defined in file {file}.")
        for (server, projects) in iterate_project_file(file).items():

            server_dir_name = get_server_dir_name(server) 
                
            fetch_projects_sonar_data(
                str(Path(output_path).joinpath(server_dir_name)),
                server,
                projects,
                component_wise
            )

    else:
        if organization == "":
            organization = "default-organization" if server != SONARCLOUD else "apache"
        fetch_organization_sonar_data(output_path, organization, server, component_wise)
