from .sonar_object import SonarObject

"""
Class representing 1 Project as a Component
"""
class ComponentProject(SonarObject):
    def __init__(self, server, project):
        SonarObject.__init__(
            self,
            endpoint = server + "api/component/show",
            params =    {
                'component': project
            },
            output_path = None
        )

    def get_organization(self):
        response_dict = self._call_api()
        if response_dict is None:
            return None
        return response_dict["component"]["organization"]