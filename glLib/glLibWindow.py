from glLibLocals import *
import glLibInit
class glLibWindow:
    def __init__(self,size,fullscreen=False,icon=None,caption="glLib Window",multisample=False,position=False,vsync=True):
        self.size = size
        self.icon = icon
        self.caption = caption
        if icon == None:icon = pygame.Surface((1,1)); icon.set_alpha(0)
        pygame.display.set_icon(icon)
        pygame.display.set_caption(caption)
        self.multisample = multisample
        self.fullscreen = fullscreen
        self.vsync = vsync
        self.clear_color = (0,0,0)
        if position != False:
            if position == GLLIB_CENTER: os.environ['SDL_VIDEO_CENTERED'] = '1'
            elif type(position) == type([]): os.environ['SDL_VIDEO_WINDOW_POS'] = str(position[0])+","+str(position[1])
        if self.multisample not in [0,False,None]:
            try:
                pygame.display.gl_set_attribute(GL_MULTISAMPLEBUFFERS,1)
                pygame.display.gl_set_attribute(GL_MULTISAMPLESAMPLES,int(self.multisample))
            except:
                print("Multisampling could not be enabled")
##        else:
##            pygame.display.gl_set_attribute(GL_MULTISAMPLEBUFFERS,0)
##            pygame.display.gl_set_attribute(GL_MULTISAMPLESAMPLES,0)
        if not self.vsync:
            try:pygame.display.gl_set_attribute(GL_SWAP_CONTROL,0)
            except:print("vsync could not be disabled")
        try:
            pygame.display.gl_set_attribute(GL_STENCIL_SIZE,8)
        except:
            print("Stencil buffer initialization failed; Stencil shadowing not available")
        try:
            pygame.display.gl_set_attribute(GL_ALPHA_SIZE,8)
        except:
            print("Alpha size initialization failed; Backbuffer will not have an alpha channel.")
        self.set_fullscreen(self.fullscreen)
##        pygame.display.init()
##        pygame.font.init()
        pygame.init()
        glLibInit.glLibInternal_init()
        if GLLIB_SHADERS_AVAILABLE:
            glLibInit.glLibInternal_init_shaders()
    def set_icon(self,icon):
        if icon == None:icon = pygame.Surface((1,1)); icon.set_alpha(0)
        pygame.display.set_icon(icon)
    def set_caption(self,caption):
        self.caption = caption
        pygame.display.set_caption(caption)
    def get_caption(self):
        return self.caption
    def set_clear_color(self,color):
        if   color == GLLIB_RED: color = [1.0,0.0,0.0]
        elif color == GLLIB_ORANGE: color = [1.0,0.5,0.0]
        elif color == GLLIB_YELLOW: color = [1.0,1.0,0.0]
        elif color == GLLIB_GREEN: color = [0.0,1.0,0.0]
        elif color == GLLIB_BLUE: color = [0.0,0.0,1.0]
        elif color == GLLIB_PURPLE: color = [0.5,0.0,1.0]
        elif color == GLLIB_WHITE: color = [1.0,1.0,1.0]
        elif color == GLLIB_BLACK: color = [0.0,0.0,0.0]
        elif color in [GLLIB_GREY,GLLIB_GRAY]: color = [0.5,0.5,0.5]
        elif color == GLLIB_PINK: color = [1.0,0.5,1.0]
        elif color == GLLIB_CYAN: color = [0.0,1.0,1.0]
        if self.clear_color != color:
            glClearColor(color[0],color[1],color[2],1.0)
            self.clear_color = (color[0],color[1],color[2])
    def clear(self):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
    def flip(self):
        pygame.display.flip()
    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.set_fullscreen(self.fullscreen)
    def set_fullscreen(self,value):
        if value:self.screenflags = OPENGL|DOUBLEBUF|FULLSCREEN; self.fullscreen = True
        else:self.screenflags = OPENGL|DOUBLEBUF; self.fullscreen = False
        pygame.display.set_mode(self.size,self.screenflags)
