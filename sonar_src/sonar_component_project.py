from .sonar_object import SonarObject

"""
Class representing 1 Project as a Component
"""
class ComponentProject(SonarObject):
    def __init__(self, server, project):
        SonarObject.__init__(
            self,
            endpoint = server + "api/components/show",
            params =    {
                'component': project
            },
            output_path = None
        )

    def get_organization(self):
        response_dict = self._call_api()

        if response_dict is not None:
            return response_dict["component"]["organization"]

        # response_dict is None
        # Could be because of different versions of Web API at api/components/show
        # Try with differnt params

        self._params = {
            'key' : self._params['component']
        }

        response_dict_2 = self._call_api()
        if response_dict_2 is None:              
            return None
        return response_dict_2["component"]["organization"]
