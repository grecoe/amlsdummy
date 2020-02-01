import json

def init():
    '''
        We really have nothing to do here....this is JUST to get this 
        out. We won't need anything really other than python to run it. 
    '''
    pass

def run(raw_data):
    try:
        name = json.loads(raw_data)["name"]
        return json.dumps({"GoAway": name + "'s not here....."})
    except Exception as e:
        result = str(e)
        return json.dumps({"error": result})

if __name__ == "__main__":
    
    init()
    result = run(json.dumps( {"name": "Dave"}))
    print("RESULT:", result)
'''
import pickle, json
from azureml.core.model import Model

def init():
    global pi_estimate
    model_path = Model.get_model_path(model_name = "pi_estimate")
    with open(model_path, "rb") as f:
        pi_estimate = float(pickle.load(f))

def run(raw_data):
    try:
        radius = json.loads(raw_data)["radius"]
        result = pi_estimate * radius**2
        return json.dumps({"area": result})
    except Exception as e:
        result = str(e)
        return json.dumps({"error": result})
'''