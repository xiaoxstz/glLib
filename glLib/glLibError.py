import sys,traceback,pygame
from OpenGL import error
class glLibError(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)
def glLibTestErrors(function):
    try:
        function()
    except:
        traceback.print_exc()
        pygame.quit()
        input()
        sys.exit()
def glLibErrors(value):
    try:
        if value == True:
            error.ErrorChecker.registerChecker(None)
        elif value == False:
            error.ErrorChecker.registerChecker(lambda: None)
        elif value == GLLIB_MAX:
            error.ErrorChecker.registerChecker(None)
            logging.basicConfig(level=logging.DEBUG)
            OpenGL.FULL_LOGGING = True
    except:
        print('''Warning:
"
import OpenGL
OpenGL.ERROR_CHECKING=False
"
has been called.  glLibErrors(...) can have no effect.''')
