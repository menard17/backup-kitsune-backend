class ZoomObject:
    """Returns object for zoom setup.
    This is just meant to be called once to complete the setup for zoom
    """

    def __init__(self, base_path="/secrets"):
        """Constructor method

        :param base_path: base path where secrets are stored
        :type base_path: str
        """
        key_file_system = open(f"{base_path}/zoom_key", "r")
        key = key_file_system.readlines()[0].strip()
        self.key = key

        secret_file_system = open(f"{base_path}/zoom_secret", "r")
        secret = secret_file_system.readlines()[0].strip()
        self.secret = secret
