import json
import os

from flask import Flask
from jinja2 import Environment, FileSystemLoader

from app import app

env = Environment(
    loader=FileSystemLoader(
        os.path.abspath(
            os.path.dirname(__file__),
        )
        + "/template",
        encoding="utf8",
    )
)

if __name__ == "__main__":
    # create the directory for the json data to write later
    dummy_filename = "./data/dummy.txt"
    os.makedirs(os.path.dirname(dummy_filename), exist_ok=True)

    endpoints = {}

    for blueprint_name in app.blueprints:
        blueprint = app.blueprints[blueprint_name]

        # register a temporary app to be able to use `url_map.iter_rules()`
        # to loop through the endpoint of a certain blueprint
        tmp_app = Flask(__name__)
        tmp_app.register_blueprint(blueprint)

        metrics = []
        for i, rule in enumerate(tmp_app.url_map.iter_rules()):
            if rule.endpoint == "static":
                continue

            if "OPTIONS" in rule.methods:
                rule.methods.remove("OPTIONS")
            if "HEAD" in rule.methods:
                rule.methods.remove("HEAD")

            metrics.append(
                {
                    "methods": str(rule.methods),
                    "rule": str(rule.rule),
                    "endpoint": rule.endpoint,
                    "index": i,
                }
            )

            endpoints[rule.endpoint] = {
                "methods": str(rule.methods),
                "rule": str(rule.rule),
            }

        template = env.get_template("dashboard.j2")
        with open(f"./data/dashboard-{blueprint_name}.json", "w") as f:
            f.write(
                template.render(metrics=metrics, blueprint={"name": blueprint_name})
            )

    with open("data/blueprints.json", "w") as f:
        f.write(json.dumps({"values": [name for name in app.blueprints]}, indent=2))

    with open("data/endpoints.json", "w") as f:
        f.write(json.dumps(endpoints, indent=2))
