from glLib import *

Screen = [800,600]

Window = glLibWindow(Screen,fullscreen=False,caption="",multisample=True,position=GLLIB_CENTER,vsync=False)
View3D = glLibView3D((0,0,Screen[0],Screen[1]),45,0.1,20.0)

Light1 = glLibLight(1)
Light1.enable()
Light1.set_ambient([0,0,0])
Light1.set_diffuse([1.0,1.0,1.0])
Light1.set_specular([1.0,1.0,1.0])
Light1.set_pos([0.0,100.0,0.01])
Light1.set_type(GLLIB_POINT_LIGHT)

glEnable(GL_LIGHTING)
glEnable(GL_TEXTURE_2D)

Shader = glLibShader()
Shader.render_equation("""
""")
print Shader.compile()

camerarot = [0,0]
cameraradius = 3.0
def quit():
    pygame.quit(); sys.exit()
def GetInput():
    global camerarot, cameraradius
    key = pygame.key.get_pressed()
    mpress = pygame.mouse.get_pressed()
    mrel = pygame.mouse.get_rel()
    for event in pygame.event.get():
        if   event.type == QUIT: quit()
        elif event.type == KEYDOWN:
            if   event.key == K_ESCAPE: quit()
        elif event.type == MOUSEBUTTONDOWN:
            if   event.button == 4: cameraradius -= 0.5
            elif event.button == 5: cameraradius += 0.5
    if mpress[0]:
        camerarot[0] += mrel[0]
        camerarot[1] += mrel[1]
def Draw():
    Window.clear()
    View3D.set_view()
    camerapos = [cameraradius*cos(radians(camerarot[0]))*cos(radians(camerarot[1])),
                 cameraradius*sin(radians(camerarot[1])),
                 cameraradius*sin(radians(camerarot[0]))*cos(radians(camerarot[1]))]
    gluLookAt(camerapos[0],camerapos[1],camerapos[2],0,0,0,0,1,0)
    Light1.set()
    
    glLibUseShader(Shader)
    
    Window.flip()
def main():
    Clock = pygame.time.Clock()
    while True:
        GetInput()
        Draw()
        Clock.tick(60)
if __name__ == '__main__': glLibTestErrors(main)
