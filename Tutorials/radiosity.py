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
    global scene_obj, radiosity_obj
    global CameraRotation, CameraRadius
    global radiosity_passes, radiosity_reduction
    global LineShader
    global drawing_patch_outlines, viewing_mode
    radiosity_reduction = 5
    radiosity_passes = 1
    radiosity_reflect = 0.5
    grid_density = 1.0/4.0
    ray_size = 10.0
    
    View3D = glLibView3D((0,0,Screen[0],Screen[1]),45,1,500)

    res = ""
##    res = "_high"
    
    scene_light = glLibObject("data/objects/cornell_box_light.obj")
    scene_obj = glLibObject("data/objects/cornell_box_scene"+res+".obj")
    scene_obj.build_list()

    print("Initializing")
    if res == "_high": intensity = 500.0
    else: intensity = 100.0
    radiosity_obj = glLibRadiosityMesh([ [scene_obj,  GLLIB_MATERIAL_DIFFUSE,[0.0,0.0,0.0],[0.2,0.2,0.2]],
                                         [scene_light,         [0.0,0.0,0.0],[intensity]*3,[0.0,0.0,0.0]] ])
    
    print("Calculating visibility")
##    radiosity_obj.compute_visibility(512)
    try:
        #Try loading the visibility data from a cached file for easy use
        radiosity_obj.use_visibility("data/cornell_box_visibility"+res+".cache")
        print('Using cached visibility data from file "data/cornell_box_visibility'+res+'.cache"')
    except IOError:
        #Just calculate the visibility data and save it for future use.  This statement
        #will not be run if the file "data/cornell_box_visibility.cache" exists.  Remove
        #it to let the radiosity calculator calculate it.  At 512 resolution, it will
        #require a lot of calculations, and consequently will take a while!
        radiosity_obj.compute_visibility(512)
        radiosity_obj.save_visibility("data/cornell_box_visibility"+res+".cache")
        print('Visibility data cached in "data/cornell_box_visibility'+res+'.cache" for the future.')
    
    print("Calculating radiosity")
##    radiosity_obj.calculate(GLLIB_RADIOSITY_RATIO,1.0/1000.0)
    radiosity_obj.calculate(GLLIB_RADIOSITY_ITERATIONS,2500)
##    radiosity_obj.calculate(GLLIB_RADIOSITY_ITERATIONS,1)

##    radiosity_obj.set_gamma(2.2)
    
    print("Building list")
    radiosity_obj.build_list_patches()
    radiosity_obj.build_list_vertices()
    
    print("Done!")

    glEnable(GL_LIGHTING)

    CameraRotation = [-90,0]
    CameraRadius = 20.0
    drawing_patch_outlines = False
    viewing_mode = 1

    glEnable(GL_LIGHTING)
    Light1 = glLibLight(1)
    Light1.set_pos([0,5,0])
    Light1.set_type(GLLIB_POINT_LIGHT)
    Light1.enable()

    pygame.mouse.get_rel()

    LineShader = glLibShader()
    LineShader.render_equation("color.rgb = vec3(0.0);")
    errors = LineShader.compile()
    print(errors)
        
def quit():
    global scene_obj
    glDisable(GL_LIGHTING)
    del scene_obj

def GetInput():
    global CameraRadius
    global drawing_patch_outlines, viewing_mode
    mrel = pygame.mouse.get_rel()
    mpress = pygame.mouse.get_pressed()
    for event in pygame.event.get():
        if   event.type == QUIT: quit(); pygame.quit(); sys.exit()
        elif event.type == KEYDOWN:
            if   event.key == K_ESCAPE: return False
            elif event.key == K_o: drawing_patch_outlines = not drawing_patch_outlines
            elif event.key == K_v: viewing_mode = 3 - viewing_mode
        elif event.type == MOUSEBUTTONDOWN:
            if   event.button == 5: CameraRadius += .2
            elif event.button == 4: CameraRadius -= .2
    if mpress[0]:
        CameraRotation[0] += mrel[0]
        CameraRotation[1] += mrel[1]
def transform_scene():
    glScalef(5.0,5.0,5.0)
def draw_scene():
    glPushMatrix()
    transform_scene()
    if viewing_mode == 1:
        radiosity_obj.draw_list_patches()
##        radiosity_obj.draw_direct_patches()
    else:
        radiosity_obj.draw_list_vertices()
##        radiosity_obj.draw_direct_vertices()
    glPopMatrix()
depthmap = None
def Draw(Window):
    Window.clear()
    View3D.set_view()
    camerapos = [0 + CameraRadius*cos(radians(CameraRotation[0]))*cos((radians(CameraRotation[1]))),
                 0 + CameraRadius*sin((radians(CameraRotation[1]))),
                 0 + CameraRadius*sin(radians(CameraRotation[0]))*cos((radians(CameraRotation[1])))]
    gluLookAt(camerapos[0],camerapos[1],camerapos[2], 0,0,0, 0,1,0)

##    radiosity_obj.calculate(0.00001,max_iter=1)
    draw_scene()
    
    if drawing_patch_outlines:
        glLibUseShader(LineShader)
        glDepthFunc(GL_LEQUAL)
        glLineWidth(2)
        glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
        draw_scene()
        glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
        glLineWidth(1)
        glDepthFunc(GL_LESS)
        glLibUseShader(None)
    
##    patch_view = glLibView3D([0,0,128,128],90.0,0.1,1.0)
##    poly1num = 0
##    camera_pos = sc_vec(5.0,radiosity_obj.patches[poly1num].center)
##    center = vec_add(radiosity_obj.patches[poly1num].norm,camera_pos)
##    up = list(radiosity_obj.patches[poly1num].tangent)

##    point_quads = glLibGetFrustumPoints(patch_view,camera_pos,center,up)
##    patch_view = glLibView3D([0,0,128,128],90.0,0.1,1000.0)
##    glDisable(GL_TEXTURE_2D)
##    glDisable(GL_LIGHTING)
##    glPointSize(4)
##    glBegin(GL_POINTS)
##    for point_quad in point_quads:
##        for point in point_quad:
##            glVertex3f(*point)
##    glEnd()
##    glPointSize(1)
##    glEnable(GL_LIGHTING)
##    glEnable(GL_TEXTURE_2D)

    Light1.set()
    Light1.draw_as_point(10)

##    glEnable(GL_SCISSOR_TEST)
##    patch_view.set_view()
##    Window.clear()
##    gluLookAt(camera_pos[0],camera_pos[1],camera_pos[2],center[0],center[1],center[2],up[0],up[1],up[2])
##    draw_scene()
##    glDisable(GL_SCISSOR_TEST)

    Window.flip()
