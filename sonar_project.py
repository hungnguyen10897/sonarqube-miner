import pandas as pd
from pathlib import Path
from sonar_object import SonarObject
from route_config import RequestsConfig

class Projects(SonarObject):
    def __init__(self, server, organization, output_path):
        SonarObject.__init__(
            self,
            endpoint = server + "api/components/search",
            params =    {
                'p': 1,     # page/iteration
                'ps': 100,  # pageSize
                'organization': organization,
                'qualifiers': 'TRK'
            },
            output_path = output_path
        )

    def _write_to_csv(self):
        projects = []
        for project in self._element_list:
            project_var = (project.values())
            projects.append(project_var)

        if projects:
            headers = list(self._element_list[0].keys())
            output_path = Path(self._output_path).joinpath("projects")
            output_path.mkdir(parents=True, exist_ok=True)
            file_path = output_path.joinpath("projects.csv")
            df = pd.DataFrame(data=projects, columns=headers)
            df.to_csv(file_path, index=False, header=True)
