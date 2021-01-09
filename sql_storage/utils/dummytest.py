

class Dummy:

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        #ttysetattr etc goes here before opening and returning the file object
        print("Entered object", self.name)
        return self

    def __exit__(self, type, value, traceback):
        #Exception handling here
        print("T", type)
        print("v", value)
        print("TB", traceback)
        print("Left object", self.name)
