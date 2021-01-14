from sonar_object import SonarObject

class Rules(SonarObject):

    def __init__(self, server, organization):
        SonarObject.__init__(
            self,
            endpoint = server + "api/rules/search",
            params =    {
                'p': 1,     # page/iteration
                'ps': 100,  # pageSize
                'organization': organization,
            },
            output_path = None
        )

    @staticmethod
    def get_rule_keys(rule_dict):
        rule_keys = []
        for rule in rule_dict:
            rule_keys.append(rule['key'])
        return rule_keys

    def get_server_rules(self):
        self._query_server(key="rules", format_function=Rules.get_rule_keys)
        return self._element_list

