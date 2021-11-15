import json

from app import app

if __name__ == "__main__":
    """
    This is a script that outputs the terraform variables.tf file for the kitsune-backend-metrics
    It print a map of:
    {
        <:metric_name>: {
            "methods": <:methods> // eg. {'POST', 'GET'}
            "rule": <:path> // eg. /payments/payment-intent
        },
        ...
    }
    You can copy the value here to the "default" value for the terraform variable "endpoints"
    """
    metric_values = {}
    for rule in app.url_map.iter_rules():
        if "OPTIONS" in rule.methods:
            rule.methods.remove("OPTIONS")
        if "HEAD" in rule.methods:
            rule.methods.remove("HEAD")

        metric_values[rule.endpoint] = {
            "methods": str(rule.methods),
            "rule": str(rule.rule),
        }

    print(json.dumps(metric_values, indent=2))
