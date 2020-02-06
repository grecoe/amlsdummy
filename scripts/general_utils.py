import pickle


def createPickle(file_name):
    '''
        Create a dummy pickle file
    '''
    my_data = {"nothing" : "to see here"}
    with open(file_name, 'wb') as model_file:
        pickle.dump(my_data, model_file)

