# See https://cloud.google.com/logging/docs/agent/logging/configuration#special-fields
def add_gcp_fields(logger, log_method, event_dict):
    event_dict["severity"] = event_dict["level"]
    del event_dict["level"]
    event_dict["message"] = event_dict["event"]
    del event_dict["event"]
    event_dict["time"] = event_dict["timestamp"]
    del event_dict["timestamp"]
    return event_dict
