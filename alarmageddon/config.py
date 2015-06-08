"""Configuration object used by Alarmageddon"""

import json


class Config(dict):
    """Alarmageddon configuration object.

    A configuration object that both acts like a read-only dictionary and
    provides some methods to access application specific settings

    :param dictionary: A dictionary of the form {'env':{config options},...}
    :param environment_name: The environment that this Config object belongs to

    """
    ENVIRONMENT_KEY = 'environment'

    def __init__(self, dictionary, environment_name):
        super(Config, self).__init__(self, **dictionary)
        self._environment_name = environment_name
        try:
            config = self[Config.ENVIRONMENT_KEY][environment_name]
            self.environment_config = config
        except KeyError:
            raise ValueError(
                "environment: '%s' was not found in configuration"
                % environment_name)

    @staticmethod
    def from_file(config_path, environment_name):
        """Load a Config object from a file

        An environment_name must be provided so that the resulting Config
        object can provide access to environment specific settings.

        """
        with open(config_path, 'r') as config_file:
            return Config(json.load(config_file), environment_name)

    def hostname(self, alias):
        """Returns an environment-specific hostname given its alias.

        host names are pulled from the hosts dictionary under each of the
        environment dictionaries.

        """
        try:
            return self.environment_config['hosts'][alias]['url']
        except:
            raise KeyError("No base URL defined for alias: %s" % alias)

    def environment_name(self):
        """returns current environment name"""
        return self._environment_name

    def test_results_file(self):
        """returns the location of the test results file"""
        return self['test_results_file']

    def __str__(self):
        """Return a string representation of this Config object"""
        return self.__repr__()

    def __repr__(self):
        return "Current Environment: %s Dictionary: %s" % (
            self._environment_name, dict.__str__(self))
