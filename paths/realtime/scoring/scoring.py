import json

def init():
    '''
        Called when an instance of the container is stood up. 

        Typically this is where the model file (pkl) is deserialized, 
        but for this example we aren't even going to use it. 
    '''
    pass

def run(raw_data):
    '''
        Entry point for REST API when calling the service.
    '''
    try:
        name = json.loads(raw_data)["name"]
        return json.dumps({"GoAway": name + "'s not here....."})
    except Exception as e:
        result = str(e)
        return json.dumps({"error": result})


if __name__ == "__main__":
    '''
        Test the funcitonality when file run
        on it's own.
    '''
    init()
    result = run(json.dumps( {"name": "Dave"}))
    print("RESULT:", result)
