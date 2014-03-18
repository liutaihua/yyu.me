import pylibmc

def get_mc():
    return pylibmc.Client(['127.0.0.1:11211'])
