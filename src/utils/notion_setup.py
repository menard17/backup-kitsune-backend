from notion_client import Client

NOTION_VERSION = "2022-06-28"


class NotionSingleton:
    """Returns singleton object for notion.
    This is just meant to be called once to complete the setup for notion

    Ref: https://www.tutorialspoint.com/python_design_patterns/python_design_patterns_singleton.htm
    """

    _instance = None

    def __init__(self):
        raise Exception("Notion is already initialiazed")

    @classmethod
    def client(cls, base_path="") -> Client:
        if cls._instance is None:
            fs_notion_key = open(f"{base_path}/notion_key/notion_key", "r")
            notion_key = fs_notion_key.readlines()[0].strip()
            cls._instance = Client(auth=notion_key, notion_version=NOTION_VERSION)
        return cls._instance
