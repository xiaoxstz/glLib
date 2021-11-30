#IMPORTANT:
#THIS ITSELF IS NOT A TUTORIAL; IT IS CODE THAT ALLOWS YOU TO VIEW TUTORIALS.
#THE TUTORIALS ARE AVAILABLE IN Tutorials/ IN THE MAIN DIRECTORY.  SEE
#TUTORIAL 1 (tutorials/objload.py) FOR MORE INFORMATION.

multisample = False
benchmark = False

try:
    import psyco
    psyco.full()
except:
    print("If you get Psyco, these tutorials may run more quickly.")
from glLib import *
sys.path.append("Tutorials")

import basiclighting
import celshading
import causticmapping
import cloth
import cubemapping
import cubeshadowmapping
import fakeao
import filters
import fluids
import framebuffer
##import framebuffermultisample
import metaballs
import normalmapping
import objload
import parallaxmapping
import particles
import pencilshading
##import physics3
import rawload
import radiosity
import shaderdrawing
import shadowmapping
import shadowstencil
import sss
import texturetechniques
import transmission
import volumetriclighting
import volumecaustics

import experiment_normalshadowmapping
import experiment_softshadow
import experiment_fakedepthoffield
import experiment_dfshadowmapping
import experiment_occludons

Screen = (800,600)
#Adjusting multisampling makes most things look nicer.  Breaks some tutorials.
Window = glLibWindow(Screen,caption="OpenGL Library Demo: Tutorials.py",multisample=multisample,position=GLLIB_CENTER,vsync=not benchmark)

versions = glLibGetVersions()
infos = glLibGetInfo()
print    ("Vendor:             "+infos["Vendor"])
print    ("Renderer:           "+infos["Renderer"])
print 
print    ("glLib version:      "+versions["glLib"])
print    ("OpenGL version:     "+versions["OpenGL"])
if "GLSL" in versions.keys():
    print("GLSL version:       "+versions["GLSL"])
print    ("PyOpenGL version:   "+versions["PyOpenGL"])

RunningDemo = False

View2D = glLibView2D((0,0,Screen[0],Screen[1]))

BackgroundTexture = glLibTexture2D("data/DemoBackground.png",[0,0,800,600],GLLIB_RGB)

buttonsize = (170,48)
hbuttonsize = (buttonsize[0]/2,buttonsize[1]/2)
buttonrect = (0,0,buttonsize[0],buttonsize[1])
buttonsurf = pygame.Surface(buttonsize).convert_alpha()
buttonsurf.fill((0,0,0))
buttonsurfhover = pygame.Surface(buttonsize).convert_alpha()
buttonsurfhover.fill((20,20,0))
pygame.draw.rect(buttonsurf,(255,255,255),buttonrect,1)
pygame.draw.rect(buttonsurfhover,(255,255,255),buttonrect,1)

Font = pygame.font.SysFont("Times New Roman",12)

Buttons = []
class Button:
    def __init__(self,pos,text,filename,demo):
        self.pos = pos
        self.hovering = False
        self.surf = buttonsurf.copy()
        self.surfhover = buttonsurfhover.copy()
        self.text = text
        self.filename = filename
        self.surftext = Font.render(text,True,(255,255,255))
        self.surftexthover = Font.render(text,True,(255,255,0))
        self.surf.blit(self.surftext,(hbuttonsize[0]-(self.surftext.get_width()/2),hbuttonsize[1]-(self.surftext.get_height()/2)))
        self.surfhover.blit(self.surftexthover,(hbuttonsize[0]-(self.surftexthover.get_width()/2),hbuttonsize[1]-(self.surftexthover.get_height()/2)))
        self.texture = glLibTexture2D(self.surf,buttonrect,GLLIB_RGBA)
        self.texturehover = glLibTexture2D(self.surfhover,buttonrect,GLLIB_RGBA)
        self.list = glLibQuad(buttonrect,self.texture)
        self.listhover = glLibQuad(buttonrect,self.texturehover)
        self.demo = demo
    def draw(self):
        glTranslatef(self.pos[0],self.pos[1],0)
        if self.hovering: self.listhover.draw()
        else:             self.list.draw()
        glTranslatef(-self.pos[0],-self.pos[1],0)
columns = 4
rows = 8
buttons_param = [
                 ["Objects .obj",objload,"objload"],
                 ["Objects .raw",rawload,"rawload"],
                 ["Shader Drawing",shaderdrawing,"shaderdrawing"],
                 ["Basic Lighting",basiclighting,"basiclighting"],
                 ["Texture Techniques",texturetechniques,"texturetechniques"],
                 ["Normal Mapping",normalmapping,"normalmapping"],
                 ["Parallax Mapping",parallaxmapping,"parallaxmapping"],
                 ["Stencil Shadows",shadowstencil,"shadowstencil"],
                 ["Shadow Mapping",shadowmapping,"shadowmapping"],
                 ["Framebuffer",framebuffer,"framebuffer"],
##                 ["FBO Multisample",framebuffermultisample,"framebuffermultisample"],
                 ["Fake AO",fakeao,"fakeao"],
                 ["Volumetric Lighting",volumetriclighting,"volumetriclighting"],
                 ["Cube Mapping",cubemapping,"cubemapping"],
                 ["Cube Shadow Mapping",cubeshadowmapping,"cubeshadowmapping"],
                 ["Transmission",transmission,"transmission"],
                 ["Subsurface Scatter",sss,"sss"],
                 ["Caustic Mapping",causticmapping,"causticmapping"],
                 ["Volumetric Caustics",volumecaustics,"volumecaustics"],
                 ["Filters",filters,"filters"],
                 ["Metaballs",metaballs,"metaballs"],
                 ["Cel Shading",celshading,"celshading"],
                 ["Pencil Shading",pencilshading,"pencilshading"],
                 ["GPU Particles",particles,"particles"],
                 ["GPU Cloth",cloth,"cloth"],
                 ["GPU Fluids",fluids,"fluids"],
##                 ["Physics",physics3,"physics3"]
                 ["Radiosity",radiosity,"radiosity"],
                 ["(X) Depth of Field",experiment_fakedepthoffield,"experiment_fakedepthoffield"],
                 ["(X) Soft Shadows",experiment_softshadow,"experiment_softshadow"],
                 ["(X) Normal Shadow Mapping",experiment_normalshadowmapping,"experiment_normalshadowmapping"],
                 ["(X) DF Shadowmapping",experiment_dfshadowmapping,"experiment_dfshadowmapping"],
                 ["(X) Occludons",experiment_occludons,"experiment_occludons"]
                 ]

x_margin = 30+(buttonsize[0]/2.0)
xspace = float(Screen[0]-(2*x_margin))/(columns-1.0)
yspace = float(Screen[1])/(rows+1.0)
position = [x_margin,Screen[1]-yspace]
index = 0
for column in range(columns):
    position[1] = Screen[1]-yspace
    for row in range(rows):
        if len(buttons_param) > index:
            button_param = buttons_param[index]
            buttonpos = [position[0]-(buttonsize[0]/2.0),position[1]-(buttonsize[1]/2.0)]
            Buttons.append(Button(list(map(rndint,buttonpos)),str(index+1)+": "+button_param[0],button_param[2],button_param[1]))
        index += 1
        position[1] -= yspace
    position[0] += xspace
    
def quit(): pygame.quit(); sys.exit()

def GetInput():
    global RunningDemo, Demo
    if not RunningDemo:
        mpos = list(pygame.mouse.get_pos())
        mpos[1] = Screen[1]-mpos[1]
        for event in pygame.event.get():
            if event.type == QUIT: quit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE: quit()
            if event.type == MOUSEBUTTONDOWN:
                for b in Buttons:
                    if b.hovering:
                        RunningDemo = True
                        Demo = b.demo
                        Demo.init(Screen)
                        Window.set_caption("OpenGL Library Demo: "+b.text.split(": ")[1]+" (Tutorials/"+b.filename+".py)")
        for b in Buttons:
            b.hovering = False
            if mpos[0] > b.pos[0] and mpos[0] < b.pos[0]+buttonsize[0]:
                if mpos[1] > b.pos[1] and mpos[1] < b.pos[1]+buttonsize[1]:
                    b.hovering = True
    if RunningDemo:
        if Demo.GetInput()==False:
            Demo.quit()
            RunningDemo = False
            Window.set_caption("OpenGL Library Demo: Tutorials.py")
def Draw():
    if not RunningDemo:
##        glClearColor(0.2,0.2,0.2,1.0)
        Window.clear()
##        glClearColor(0.0,0.0,0.0,1.0)
        View2D.set_view()
        glLibSelectTexture(BackgroundTexture)
        glLibDrawScreenQuad(texture=True)
        glLibAlpha(0.3)
        glTranslatef(0,0,0.1)
        for b in Buttons: b.draw()
        glLibAlpha(1.0)
        Window.flip()
    else:
        Demo.Draw(Window)

def main():
    Clock = pygame.time.Clock()
    if benchmark:
        glLibErrors(False)
    while True:
        GetInput()
        Draw()
        if benchmark:
            Clock.tick()
            print("fps: %f" % round(Clock.get_fps(),2))
        else:
            Clock.tick(60)
if __name__ == '__main__':
    glLibTestErrors(main)
