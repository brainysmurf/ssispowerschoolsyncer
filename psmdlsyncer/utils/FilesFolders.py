import os

def clear_folder(path, exclude=None):
    """
    Removes any file with folder path
    Also, if not there, creates it

    exclude can be a function, it is passed the file name (without the path info)
    
    """
    if not os.path.exists(path):
        os.mkdir(path)
    for f in os.listdir(path):
        if not os.path.isdir(path + '/' + f):
            if exclude and callable(exclude):
                if not exclude(f):
                    os.remove(path + '/' + f)
            else:
                os.remove(path + '/' + f)

if __name__ == "__main__":

    here = os.path.realpath(__file__)
    split = here.split('/')
    up = '/'.join(split[:-1])
    clear_folder(up + '/' + 'test')
