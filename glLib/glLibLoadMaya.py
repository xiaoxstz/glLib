from glLibLocals import *

class node:
    def __init__(self,name):
        self.name = name
def glLibInternal_LoadRAWFile(filename):
    #http://caad.arch.ethz.ch/info/maya/manual/FileFormats/FileFormats.fm.html#9613
    if filename.endswith("mb"):
        file = open(filename,"rb")
    else:
        file = open(filename,"r")
    for line in file:
        if line.startswith("//"): continue
##        if line.startswith("currentUnit"):
##            -l cm -a deg -t ntsc;

        

    return face_type, \
           vertices, [], faces, [vertices], \
           [[]], [[]], [[]], \
           [], \
           False, False, False

    

