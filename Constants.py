import os

def get_path_relative(add):
    """
    Derive the path from this file's location, and add 'add' to it
    """
    full_path = os.path.realpath(__file__)
    split = full_path.split('/')
    split = split[:-2] # up one level
    split.append(add) # add to path
    return '/'.join(split)

k_homerooms = ['6L', '6E', '6A', '6R', '6N', '6S', '7L', '7E', '7A', '7R', '7N', '7SWA', '8L', '8E', '8A', '8R', '8N', '8S', '9L', '9E', '9A', '9R', '9N', '9SWA', '10L', '10E', '10A', '10R', '10N', '10S', '10SWA', '11L', '11E', '11A', '11R', '11N', '12L', '12E', '12A', '12R', '12N']

if os.path.exists('/home/powerschool'):
    # We must be on the server itself
    k_path_to_powerschool = '/home/powerschool'
else:
    # We are coding from a laptop/desktop
    # Derive the path to powerschool relative to
    # this file's location
    k_path_to_powerschool = get_path_relative('powerschool')

k_path_to_databases = get_path_relative('databases')
k_path_to_output = get_path_relative('output')
k_path_to_errors = get_path_relative('errors')
k_path_to_uploads = get_path_relative('uploads')
