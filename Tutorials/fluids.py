#Tutorial by Ian Mallett

#Controls:
#ESC           - Return to menu
#n             - Toggles using/not using normalmap
#r             - Cycle among reflection, refraction, both
#LCLICK + DRAG - Rotate camera
#RCLICK + DRAG - Rotate spaceship
#SROLL WHEEL   - Zoom

#Theory:


import sys,os
sys.path.append(os.path.split(sys.path[0])[0])
from glLib import *

def init(Screen):
    global View3D
    global Light1
    global fluid, Plane
    global fluid_res,dimensions
    global CameraRotation, CameraRadius
    
    View3D = glLibView3D((0,0,Screen[0],Screen[1]),45,0.01,500)

##    fluid_res = [64,64]
    fluid_res = [128,128]
##    fluid_res = [256,256]
##    fluid_res = [512,512]
##    fluid_res = [1024,1024]
##    fluid_res = [4,4,4]
##    fluid_res = [16,16,16]
##    fluid_res = [32,32,32]
##    fluid_res = [64,64,64]
    dimensions = len(fluid_res)
    fluid = glLibFluidGasGPU(fluid_res)

    #Load the Floor
    FloorTexture = glLibTexture2D("data/floor.jpg",[0,0,512,512],GLLIB_RGBA,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    try:FloorTexture.anisotropy(GLLIB_MAX)
    except:pass
    Plane = glLibPlane(5,(0,1,0),FloorTexture,10)

    glEnable(GL_LIGHTING)

    CameraRotation = [90,89.99]
    CameraRadius = 2.0
    drawing_patch_outlines = False
    viewing_mode = 1

    glEnable(GL_LIGHTING)
    Light1 = glLibLight(1)
    Light1.set_pos([0,500,0])
    Light1.set_type(GLLIB_POINT_LIGHT)
    Light1.enable()

    pygame.mouse.get_rel()
        
def quit():
    glDisable(GL_LIGHTING)

def GetInput():
    global CameraRadius, mpress, mpos, mrel
    for event in pygame.event.get():
        if   event.type == QUIT: quit(); pygame.quit(); sys.exit()
        elif event.type == KEYDOWN:
            if   event.key == K_ESCAPE: return False
            elif event.key == K_r: fluid.reset()
        elif event.type == MOUSEBUTTONDOWN:
            if   event.button == 5: CameraRadius += .2
            elif event.button == 4: CameraRadius -= .2
    mrel = pygame.mouse.get_rel()
    mpress = pygame.mouse.get_pressed()
    mpos = pygame.mouse.get_pos()
    key = pygame.key.get_pressed()
    if key[K_LCTRL] or key[K_RCTRL]:
        if mpress[0]:
            CameraRotation[0] += mrel[0]
            CameraRotation[1] += mrel[1]
            mpress = None
def draw_scene():
    glPushMatrix()
    glTranslatef(0.0,0.001,0.0)
    if dimensions == 3:
        glTranslatef(0.0,0.5,0.0)
    fluid.draw(View3D)
    glPopMatrix()
mouse_pos = [0.0,0.0,0.0]
previous_mouse_pos = [0.0,0.0,0.0]
def Draw(Window):
    global mouse_pos, previous_mouse_pos
    Window.clear()
    View3D.set_view()
    camerapos = [0 + CameraRadius*cos(radians(CameraRotation[0]))*cos((radians(CameraRotation[1]))),
                 0 + CameraRadius*sin((radians(CameraRotation[1]))),
                 0 + CameraRadius*sin(radians(CameraRotation[0]))*cos((radians(CameraRotation[1])))]
    gluLookAt(camerapos[0],camerapos[1],camerapos[2], 0,0,0, 0,1,0)

    Light1.set()
    Light1.draw_as_point(10)

    Plane.draw()

    previous_mouse_pos = list(mouse_pos)
    mouse_pos = list(glLibGetPosAt(mpos))
    if mpress != None:
        mouse_coord = list(mouse_pos)
        mouse_coord[0] += 0.5
        mouse_coord[2] += 0.5
        if mouse_coord[0] > 0.0 and mouse_coord[0] < 1.0:
            if mouse_coord[2] > 0.0 and mouse_coord[2] < 1.0:
                if   dimensions == 2:
                    coord = vec_mult(fluid_res,[mouse_coord[0],    1.0-mouse_coord[2]])
                    coord = vec_subt(coord,[0.5,0.5])
                    coord = list(map(rndint,coord))
                    coord = vec_add(coord,[0.5,0.5])
                elif dimensions == 3:
                    coord = vec_mult(fluid_res,[mouse_coord[0],0.0,    mouse_coord[2]])
                    coord = vec_subt(coord,[0.5,-0.5,0.5])
                    coord = list(map(rndint,coord))
                    coord = vec_add(coord,[0.5,-0.5,0.5])
                if mpress[0]:
                    fluid.add_density_at(coord,[1.0,1.0,1.0])
                    fluid.add_force_at(coord,[0.0,1.0,0.0])
                if mpress[2]:
                    force = [   mouse_pos[0]-previous_mouse_pos[0],
                                0.0,
                              -(mouse_pos[2]-previous_mouse_pos[2]) ]
                    if dimensions == 2:
                        force = [force[0],force[2]]
                    force = sc_vec(5.0,force)
                    fluid.add_force_at(coord,force)
    fluid.step(20,4.5)

    draw_scene()

    Window.flip()
