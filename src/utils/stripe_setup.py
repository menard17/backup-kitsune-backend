class StripeSingleton:
    """Returns singleton object for stripe.
    This is just meant to be called once to complete the setup for stripe

    Ref: https://www.tutorialspoint.com/python_design_patterns/python_design_patterns_singleton.htm
    """

    _instance = None

    def __init__(self, stripe, base_path="/secrets"):
        """Constructor method

        :param base_path: base path where secrets are stored
        :type base_path: str
        """
        if StripeSingleton._instance is not None:
            raise Exception("Stripe is already initialiazed")
        else:
            StripeSingleton._instance = self
            file_system = open(f"{base_path}/stripe_key", "r")
            key = file_system.readlines()[0].strip()
            stripe.api_key = key
