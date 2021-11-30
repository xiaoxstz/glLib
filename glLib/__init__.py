import os,sys
old_path = sys.path

parentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,parentdir) 

from glLibMain import *

sys.path = old_path
