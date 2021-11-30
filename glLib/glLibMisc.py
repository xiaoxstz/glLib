from glLibLocals import *
from glLibTexturing import *
from glLibView import glLibView2D
from glLibShader import glLibUseShader
from glLibMath import *
def glLibGetTimeElements(sec):
    seconds=sec; minutes=0; hours=0; days=0
    while seconds >= 60: seconds -= 60; minutes += 1
    while minutes >= 60: minutes -= 60; hours += 1
    while hours >= 24: hours -= 24; days += 1
    return seconds, minutes, hours
def glLibScreenSurf(rect=GLLIB_AUTO,type=GLLIB_RGB,framebuffer=0):
    if rect == GLLIB_AUTO:
        size = glGetFloatv(GL_VIEWPORT)
        size = [int(round(size[2])),int(round(size[3]))]
        rect = [0,0,size[0],size[1]]
    glPixelStorei(GL_PACK_ROW_LENGTH,0)
    glPixelStorei(GL_PACK_SKIP_ROWS,0)
    glPixelStorei(GL_PACK_SKIP_PIXELS,0)
    if type==GLLIB_RGBA:
        glPixelStorei(GL_PACK_ALIGNMENT,4)
    elif type==GLLIB_RGB:
        glPixelStorei(GL_PACK_ALIGNMENT,1)
    elif type==GLLIB_DEPTH:
        glPixelStorei(GL_PACK_ALIGNMENT,1)
    try:
        if type==GLLIB_DEPTH:
            data = glReadPixels(rect[0],rect[1],rect[2],rect[3],type,GL_FLOAT)
        else:
            data = glReadPixels(rect[0],rect[1],rect[2],rect[3],type,GL_UNSIGNED_BYTE)
##        print len(data)
    except:
        previous = glGetIntegerv(GL_READ_BUFFER)
        if type==GLLIB_DEPTH:
            glReadBuffer(GL_DEPTH_ATTACHMENT_EXT)
            data = glReadPixels(rect[0],rect[1],rect[2],rect[3],GL_DEPTH_COMPONENT,GL_FLOAT)
        else:
            glReadBuffer(GL_COLOR_ATTACHMENT0_EXT+framebuffer)
            data = glReadPixels(rect[0],rect[1],rect[2],rect[3],type,GL_UNSIGNED_BYTE)
        glReadBuffer(previous)
    if type==GLLIB_RGBA:
        return pygame.image.fromstring(data,(rect[2],rect[3]),'RGBA',1)
    elif type==GLLIB_RGB:
        return pygame.image.fromstring(data,(rect[2],rect[3]),'RGB',1)
    elif type==GLLIB_DEPTH:
##        data = np.reshape(data,(-1,1))
##        data = np.transpose([data,data,data])
##        data = np.reshape(data,(rect[2],rect[3],3))
        return pygame.surfarray.make_surface(data)
def glLibTextureDataSurf(texture):
    glLibSelectTexture(texture)
    texturedata = np.array(glGetTexImage(texture.type,0,texture.format,GL_FLOAT))*255.0
    texturedatasurf = pygame.surfarray.make_surface(np.fliplr(texturedata.transpose((1,0,2))))
    return texturedatasurf
def glLibInternal_save_surf(surface,path,overwrite):
    if overwrite:
        pygame.image.save(surface,path)
    else:
        path = path.split(".")
        counter = 1
        while True:
            try:
                if counter == 1:
                    pygame.image.load(path[0]+"."+path[1])
                else:
                    pygame.image.load(path[0]+str(counter)+"."+path[1])
            except:break
            counter += 1
        if counter == 1:
            pygame.image.save(surface,path[0]+"."+path[1])
        else:
            pygame.image.save(surface,path[0]+str(counter)+"."+path[1])
def glLibSaveScreenshot(path,rect=GLLIB_AUTO,type=GLLIB_RGB,framebuffer=0,overwrite=False):
    surface = glLibScreenSurf(rect,type,framebuffer)
    glLibInternal_save_surf(surface,path,overwrite)
def glLibSaveTextureData(path,texture,overwrite=False):
    surface = glLibTextureDataSurf(texture)
    glLibInternal_save_surf(surface,path,overwrite)
def glLibAlpha(alpha):
    red,green,blue = glGetFloatv(GL_CURRENT_COLOR)[:3]
    glColor4f(red,green,blue,alpha)
    
def glLibGetColorAt(windowcoord,flip=True):
    viewport = glGetIntegerv(GL_VIEWPORT)
    winX = windowcoord[0]
    if flip: winY = viewport[3]-windowcoord[1]
    return glReadPixels(winX,winY,1,1,GL_RGBA,GL_FLOAT)
def glLibGetDepthAt(windowcoord,flip=True):
    viewport = glGetIntegerv(GL_VIEWPORT)
    winX = windowcoord[0]
    if flip: winY = viewport[3]-windowcoord[1]
    return glReadPixels(winX,winY,1,1,GL_DEPTH_COMPONENT,GL_FLOAT)
def glLibGetPosAt(windowcoord,flip=True):
    viewport = glGetIntegerv(GL_VIEWPORT)
    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)
    winX = windowcoord[0]
    if flip: winY = viewport[3]-windowcoord[1]
    else: winY = windowcoord[1]
    winZ = glReadPixels(winX,winY,1,1,GL_DEPTH_COMPONENT,GL_FLOAT)
    return gluUnProject(winX,winY,winZ,modelview,projection,viewport)
def glLibGetProjectedFrom(pos,flip=True):
    viewport = glGetIntegerv(GL_VIEWPORT)
    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)
    win = gluProject(pos[0],pos[1],pos[2],modelview,projection,viewport)
    if flip: return [win[0],viewport[3]-win[1]]
    else:    return [win[0],            win[1]]
def glLibGetInfo():
    vendor = str(glGetString(GL_VENDOR))
    renderer = str(glGetString(GL_RENDERER))
    data = {}
    if vendor   != None: data["Vendor"  ] = vendor
    if renderer != None: data["Renderer"] = renderer
    return data
def glLibGetVersions():
    data = {"glLib":"0.5.9","OpenGL":glGetString(GL_VERSION).decode(),"PyOpenGL":OpenGL.__version__}
    if data["OpenGL"] != None and int(data["OpenGL"].split(".")[0]) >= 2:
        data["GLSL"] = str(glGetString(GL_SHADING_LANGUAGE_VERSION))
    if data["OpenGL"] == None:
        del data["OpenGL"]
    return data
    
def glLibSceneToTexture(rect,texture=None,format=GLLIB_RGB,filtering=False,mipmapping=False,precision=8):
    if texture==None:
        texture = glLibTexture2D(None,list(rect),format,filtering,mipmapping,precision=precision)
        texture.edge(GLLIB_CLAMP)
##        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_COMPARE_MODE,GL_COMPARE_R_TO_TEXTURE)
##        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_COMPARE_FUNC,GL_LEQUAL)
    glBindTexture(GL_TEXTURE_2D,texture.texture)
    glCopyTexImage2D(GL_TEXTURE_2D,0,format,rect[0],rect[1],rect[2],rect[3],0)
    return texture
##specialview1 = glLibView2D((0,0,1,1))
##def glLibBlur(rect,shader,radius,uvstep):
##    currenttexture = glGetIntegerv(GL_ACTIVE_TEXTURE) - GL_TEXTURE0
##
##    glLibActiveTexture(9)
##    shader.special1tex1 = glLibSceneToTexture(rect,shader.special1tex1)
##
##    specialview1.rect = rect
##    specialview1.set_view()
##
##    glLibUseShader(shader)
##    
##    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
##    glLoadIdentity()
##    glBindTexture(GL_TEXTURE_2D,shader.special1tex1.texture)
##    glUniform1i(glGetUniformLocation(shader.program,"scenebuffertex1"),9)
##    shader.pass_int(1,"stage")
##    shader.pass_vec2(uvstep,"uvstep")
##    shader.pass_int(radius,"size")
##    glLibTexFullScreenQuad()
##
##    glLibActiveTexture(10)
##    shader.special1tex2 = glLibSceneToTexture(rect,shader.special1tex2)
##    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
##    glLoadIdentity()
##    glBindTexture(GL_TEXTURE_2D,shader.special1tex2.texture)
##    glUniform1i(glGetUniformLocation(shader.program,"scenebuffertex2"),10)
##    shader.pass_int(2,"stage")
##    glLibTexFullScreenQuad()
##
##    glLibActiveTexture(currenttexture)
##specialview2 = glLibView2D((0,0,1,1))
##def glLibRadialBlur(rect,shader,center,size,step):
##    currenttexture = glGetIntegerv(GL_ACTIVE_TEXTURE) - GL_TEXTURE0
##
##    glLibActiveTexture(5)
##    shader.special2tex1 = glLibSceneToTexture(rect,shader.special2tex1)
##
##    specialview2.rect = rect
##    specialview2.set_view()
##
##    glLibUseShader(shader)
##    
##    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
##    glLoadIdentity()
##    glBindTexture(GL_TEXTURE_2D,shader.special2tex1.texture)
##    glUniform1i(glGetUniformLocation(shader.program,"scenebuffertex"),5)
##    shader.pass_int(size,"size")
##    shader.pass_float(step,"step")
##    shader.pass_vec2(center,"center")
##    glLibTexFullScreenQuad()
##
##    glLibActiveTexture(currenttexture)
##specialview3 = glLibView2D((0,0,1,1))
##def glLibThreshold(texture,shader,lowthreshold,highthreshold,replacecolor):
##    currenttexture = glGetIntegerv(GL_ACTIVE_TEXTURE) - GL_TEXTURE0
##
##    glLibActiveTexture(5)
##    shader.special3tex1 = glLibSceneToTexture(texture.rect,shader.special3tex1)
##
##    specialview3.rect = texture.rect
##    specialview3.set_view()
##
##    glLibUseShader(shader)
##    
##    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
##    glLoadIdentity()
##    glBindTexture(GL_TEXTURE_2D,shader.special3tex1.texture)
##    glUniform1i(glGetUniformLocation(shader.program,"scenebuffertex"),5)
##    shader.pass_vec4(lowthreshold,"lowthreshold")
##    shader.pass_vec4(highthreshold,"highthreshold")
##    shader.pass_vec4(replacecolor,"replacecolor")
##    glLibTexFullScreenQuad()
##
##    glLibActiveTexture(currenttexture)
def glLibOutline(drawfunc,linewidth):
    oldlinewidth = glGetIntegerv(GL_LINE_WIDTH)
    oldcullenable = glGetBooleanv(GL_CULL_FACE)
    oldcullside = glGetIntegerv(GL_CULL_FACE_MODE)
    glLineWidth(linewidth)
    glEnable(GL_CULL_FACE)
    glCullFace(GL_FRONT)
    glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
    drawfunc()
    glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
    if oldcullside == GL_BACK: glCullFace(GL_BACK)
    if not oldcullenable: glDisable(GL_CULL_FACE)
    glLineWidth(oldlinewidth)
def glLibSendTransform(shader,transformfunc,location):
    glPushMatrix()
    glLoadIdentity()
    transformfunc()
    matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
    glPopMatrix()
    shader.pass_mat4(location,matrix)
##def glLibSendInvView(shader,viewfunc):
##    glPushMatrix()
##    glLoadIdentity()
##    viewfunc()
##    matrix = np.matrix(glLibMathRotateMatrix(glLibMathGetListMatrix(glGetFloatv(GL_MODELVIEW_MATRIX)))).I
##    glPopMatrix()
##    shader.pass_mat4("viewmatrix",matrix)
def glLibInternal_set_proj_and_view_matrices(view,p1,p2):
    view.set_view()
    proj_mat = glGetFloatv(GL_PROJECTION_MATRIX)
    gluLookAt(p1[0],p1[1],p1[2],p2[0],p2[1],p2[2],0.0,1.0,0.0)
    view_mat = glGetFloatv(GL_MODELVIEW_MATRIX)
    return proj_mat,view_mat
def glLibMakeDepthMap                (     light,LightView,objpos,depthmap,drawoccluders,offset=1.0,filtering=False):
    return glLibInternal_MakeDepthMap(None,light,LightView,objpos,depthmap,drawoccluders,offset,    filtering      )
def glLibMakeDepthMapFBO             (fbo, light,LightView,objpos,         drawoccluders,offset=1.0                ):
    return glLibInternal_MakeDepthMap(fbo, light,LightView,objpos,None,    drawoccluders,offset                    )
def glLibInternal_MakeDepthMap       (fbo, light,LightView,objpos,depthmap,drawoccluders,offset,    filtering=False):
    if fbo != None: fbo.enable([1])
    
    glClear(GL_DEPTH_BUFFER_BIT)    
    glLibPushView()
    LightPosition = light.get_pos()
    LightProjectionMatrix,LightViewMatrix = glLibInternal_set_proj_and_view_matrices(LightView,LightPosition,objpos)
    glEnable(GL_POLYGON_OFFSET_FILL);glPolygonOffset(offset,offset)
    glColorMask(0,0,0,0)
    drawoccluders()
    glColorMask(1,1,1,1)
    glPolygonOffset(0.0,0.0);glDisable(GL_POLYGON_OFFSET_FILL)
    if fbo == None: depthmap = glLibSceneToTexture(LightView.rect,depthmap,format=GLLIB_DEPTH,filtering=filtering)
    glLibPopView()
    
    if fbo != None: fbo.disable()
    
    if fbo != None: return [fbo.get_texture(1),LightProjectionMatrix,LightViewMatrix]
    else:           return [depthmap,LightProjectionMatrix,LightViewMatrix]
def glLibDepthPeel                (     pos,view,objpos,num,shader,draw,textures,filtering=False):
    return glLibInternal_DepthPeel(None,pos,view,objpos,num,shader,draw,textures,filtering,     )
def glLibDepthPeelFBO             (fbos,pos,view,objpos,num,shader,draw                         ):
    return glLibInternal_DepthPeel(fbos,pos,view,objpos,num,shader,draw,None,                   )
def glLibInternal_DepthPeel       (fbos,pos,view,objpos,num,shader,draw,textures,filtering=False):
    glLibUseShader(shader)
    shader.pass_vec2("size",view.rect[2:])
    shader.pass_bool("stage1",True)

    glLibPushView()

    projmat,viewmat = glLibInternal_set_proj_and_view_matrices(view,pos,objpos)
    
    out_textures = []
    out2_textures = []
    ping_pong = 1
    for render_pass in range(num):
        if fbos != None:
            fbos[render_pass].enable(GLLIB_ALL)
        glClear(GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        view.set_view()
        gluLookAt(pos[0],pos[1],pos[2],objpos[0],objpos[1],objpos[2],0,1,0)
        glEnable(GL_POLYGON_OFFSET_FILL);glPolygonOffset(1.0,1.0)
        draw()
        glPolygonOffset(0,0);glDisable(GL_POLYGON_OFFSET_FILL)
        if fbos != None:
            fbos[render_pass].disable()
            returned_textures = fbos[render_pass].get_textures()
            out_textures.append(returned_textures[0])
            if len(returned_textures)>1:
                out2_textures.append(returned_textures[1:])
        else:
            out_textures.append(glLibSceneToTexture(view.rect,textures[render_pass],GLLIB_DEPTH,filtering,False))
        shader.pass_bool("stage1",False)
        shader.pass_texture(out_textures[-1],2)
        ping_pong = 3 - ping_pong
        
    glLibPopView()
    glLibUseShader(None)
    out3_textures = []
    for index in range(len(out_textures)):
        out3_textures.append(out_textures[index])
        try:
            for tex in out2_textures[index]:
                out3_textures.append(tex)
        except: pass
    return out3_textures,projmat,viewmat
##def glLibDepthPeelSinglePassFBO(fbo,pos,view,objpos,num,shader,draw):
##    glPushMatrix()
##    view.set_view()
##    projmat = glGetFloatv(GL_PROJECTION_MATRIX)
##    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
##    glLoadIdentity()
##    gluLookAt(pos[0],pos[1],pos[2],objpos[0],objpos[1],objpos[2],0,1,0)
##    viewmat = glGetFloatv(GL_MODELVIEW_MATRIX)
##    glLibUseShader(shader)
##    shader.pass_vec2("size",view.rect[2:])
####    shader.pass_float("near",view.near)
####    shader.pass_float("far",view.far)
##    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
##    draw()
##    glLibScreenshot("depthblah.png",rect=GLLIB_AUTO,type=GLLIB_DEPTH,framebuffer=7,overwrite=True)
##    out_textures = []
##    for tex in range(num):
##        out_textures.append(fbo.get_texture(tex+1))
##    out_textures.reverse()
##    glPopMatrix()
##    return out_textures,projmat,viewmat
def glLibUseDepthMaps(depthmaps,number,index,shader,func):
##    glLibUseShader(shader)
    for depthmapdata in depthmaps:
        if type(depthmapdata[0])==type([]):
            for depthmap in depthmapdata[0]:
                glLibActiveTexture(index)
                shader.pass_texture(depthmap,index)
                index += 1
        else:
            shader.pass_texture(depthmapdata[0],index)
            index += 1
        glMatrixMode(GL_TEXTURE)
        glPushMatrix()
        glLoadMatrixf([[0.5,0.0,0.0,0.0],
                       [0.0,0.5,0.0,0.0],
                       [0.0,0.0,0.5,0.0],
                       [0.5,0.5,0.5,1.0]])
        glMultMatrixf(depthmapdata[1])
        glMultMatrixf(depthmapdata[2])
        func()
        shader.pass_mat4("gllibinternal_depthmatrix_"+str(number),glLibMathGetListMatrix(glGetFloatv(GL_TEXTURE_MATRIX)))
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        number += 1
##fbo1,fbo2,light,lightview,objpos,num,shader,draw_receivers_func,draw_refractors_func,\
##                draw_reflectors_func,posmaps,normmaps,filtering,precision  
##def glLibUpdateCubeMapFBO(fbo,cubemapview,pos,drawreflectees,format=GLLIB_RGB,update=GLLIB_ALL):
##    glLibInternal_glLibUpdateCubeMap(cubemap,cubemapview,pos,drawreflectees,format,update)
def glLibUpdateCubeMap(cubemap,cubemapview,pos,drawreflectees,format=GLLIB_RGB,update=GLLIB_ALL):
    glLibInternal_glLibUpdateCubeMap(cubemap,cubemapview,pos,drawreflectees,format,update)
def glLibInternal_glLibUpdateCubeMap(cubemap,cubemapview,pos,drawreflectees,format,update):
    x,y,z=pos
    if update == GLLIB_ALL: update = [1,2,3,4,5,6]
    for i in update:
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        cubemapview.set_view()
        if   i == 1: gluLookAt(x,y,z, x+1,  y,  z,  0,-1, 0)
        elif i == 2: gluLookAt(x,y,z, x-1,  y,  z,  0,-1, 0)
        elif i == 3: gluLookAt(x,y,z,   x,y+1,  z,  0, 0, 1)
        elif i == 4: gluLookAt(x,y,z,   x,y-1,  z,  0, 0,-1)
        elif i == 5: gluLookAt(x,y,z,   x,  y,z+1,  0,-1, 0)
        elif i == 6: gluLookAt(x,y,z,   x,  y,z-1,  0,-1, 0)
        drawreflectees()
        glBindTexture(GL_TEXTURE_CUBE_MAP,cubemap.texture)
        glCopyTexImage2D(GLLIB_TEXTURE_CUBE_FACES[i-1],0,format,\
                         cubemapview.rect[0],cubemapview.rect[1],cubemapview.rect[2],cubemapview.rect[3],0)

def glLibPushView():
    global glLibInternal_current_view
    glLibInternal_current_view = glGetIntegerv(GL_VIEWPORT)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
def glLibPopView():
    glViewport(*glLibInternal_current_view)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    
def glLibPrepareCaustics():
    global GLLIB_CAUSTIC_POINT
    GLLIB_CAUSTIC_POINT = glLibTexture2D(os.path.join("glLib","causticpoint.png"),(0,0,83,83),GLLIB_RGBA)
    GLLIB_CAUSTIC_POINT.edge(GLLIB_CLAMP)
    return GLLIB_CAUSTIC_POINT
def glLibInternal_CausticPositionMap_drawscene(shader,draw_receivers_func,draw_refractors_func,draw_reflectors_func):
    shader.pass_int("type",2)
    draw_refractors_func()
    shader.pass_int("type",3)
    draw_reflectors_func()
    glClear(GL_DEPTH_BUFFER_BIT)
    glBlendFunc(GL_ONE,GL_ONE)
    shader.pass_int("type",1)
    draw_receivers_func()
    glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
glLibInternal_depth_tex = None
def glLibCausticPositionNormalMapFBO             (fbo1,fbo2,light,lightview,objpos,num,shader,draw_receivers_func,draw_refractors_func,draw_reflectors_func                                                       ):
    return glLibInternal_CausticPositionNormalMap(fbo1,fbo2,light,lightview,objpos,num,shader,draw_receivers_func,draw_refractors_func,draw_reflectors_func,posmaps=None,normmaps=None,filtering=False,precision=8)
def glLibCausticPositionNormalMap                (          light,lightview,objpos,num,shader,draw_receivers_func,draw_refractors_func,draw_reflectors_func,posmaps=None,normmaps=None,filtering=False,precision=8):
    return glLibInternal_CausticPositionNormalMap(None,None,light,lightview,objpos,num,shader,draw_receivers_func,draw_refractors_func,draw_reflectors_func,posmaps,     normmaps,     filtering,      precision  )
def glLibInternal_CausticPositionNormalMap       (fbo1,fbo2,light,lightview,objpos,num,shader,draw_receivers_func,draw_refractors_func,draw_reflectors_func,posmaps,     normmaps,     filtering,      precision  ):
    global glLibInternal_depth_tex
    glLibUseShader(shader)
    lightpos = light.get_pos()
##    shader.pass_vec3("lightpos",lightpos)
    shader.pass_vec2("size",lightview.rect[2:])
    outposmaps = []
    outnormmaps = []
    ping_pong = 1
    for render_pass in range(1,num+1,1):
        if fbo1 != None:
            if ping_pong == 1: fbo1.enable([1,2])#,3])
            else:              fbo2.enable([1,2])#,3])
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        lightview.set_view()
        gluLookAt(lightpos[0],lightpos[1],lightpos[2],objpos[0],objpos[1],objpos[2],0,1,0)
        shader.pass_int("render_pass",render_pass)
        if render_pass>1: shader.pass_texture(glLibInternal_depth_tex,1)
        if fbo1 == None:
            shader.pass_int("fbotype",1)
            shader.pass_bool("stage1",True)
            glLibInternal_CausticPositionMap_drawscene(shader,draw_receivers_func,draw_refractors_func,draw_reflectors_func)
            posmap = glLibSceneToTexture(lightview.rect,posmaps[render_pass-1],GLLIB_RGB)
##            glLibScreenshot("posmap"+str(render_pass)+".png",rect=GLLIB_AUTO,type=GLLIB_RGB,framebuffer=0,overwrite=True)
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
            shader.pass_bool("stage1",False)
            draw_reflectors_func(); draw_refractors_func()
            normmap = glLibSceneToTexture(lightview.rect,normmaps[render_pass-1],GLLIB_RGB)
##            glLibScreenshot("normmap"+str(render_pass)+".png",rect=GLLIB_AUTO,type=GLLIB_RGB,framebuffer=0,overwrite=True)
            glLibInternal_depth_tex = glLibSceneToTexture(lightview.rect,glLibInternal_depth_tex,GLLIB_DEPTH)
        else:
            shader.pass_int("fbotype",2)
            glLibInternal_CausticPositionMap_drawscene(shader,draw_receivers_func,draw_refractors_func,draw_reflectors_func)
##            glLibScreenshot("posmap"+str(render_pass)+".png",rect=GLLIB_AUTO,type=GLLIB_RGB,framebuffer=1,overwrite=True)
##            glLibScreenshot("normmap"+str(render_pass)+".png",rect=GLLIB_AUTO,type=GLLIB_RGB,framebuffer=2,overwrite=True)
##            glLibScreenshot("depth"+str(render_pass)+".png",rect=GLLIB_AUTO,type=GLLIB_DEPTH,framebuffer=3,overwrite=True)
            if ping_pong == 1:
                fbo1.disable()
                posmap = fbo1.get_texture(1); normmap = fbo1.get_texture(2)
##                glLibInternal_depth_tex = fbo1.get_texture(3)
            else:
                fbo2.disable()
                posmap = fbo2.get_texture(1); normmap = fbo2.get_texture(2)
##                glLibInternal_depth_tex = fbo2.get_texture(3)
            ping_pong = 3 - ping_pong
        outposmaps.append(posmap)
        outnormmaps.append(normmap)
    glLibUseShader(None)
    return [outposmaps,outnormmaps]
def glLibCausticMap                (     light,lightview,objpos,objtransform,shader,causticgrid,causticgridscalar,particlesize,particlecolordata,posmaps,normmaps,causticmap=None,filtering=False,precision=8):
    return glLibInternal_CausticMap(None,light,lightview,objpos,objtransform,shader,causticgrid,causticgridscalar,particlesize,particlecolordata,posmaps,normmaps,causticmap,     filtering,      precision  )
def glLibCausticMapFBO             (fbo, light,lightview,objpos,objtransform,shader,causticgrid,causticgridscalar,particlesize,particlecolordata,posmaps,normmaps,                                           ):
    return glLibInternal_CausticMap(fbo, light,lightview,objpos,objtransform,shader,causticgrid,causticgridscalar,particlesize,particlecolordata,posmaps,normmaps,None,           False,          None       )
def glLibInternal_CausticMap       (fbo, light,lightview,objpos,objtransform,shader,causticgrid,causticgridscalar,particlesize,particlecolordata,posmaps,normmaps,causticmap,     filtering,      precision  ):
    lightpos = light.get_pos()
    if fbo != None:
        fbo.enable([1])
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    View2D = glLibView2D(lightview.rect)
    View2D.set_view()
    glLibUseShader(shader)
    shader.pass_vec2("size",lightview.rect[2:])
    shader.pass_float("grid_sc",causticgridscalar)
    
    glLibPushView()
    glLoadIdentity()
    lightview.set_view()
    gluLookAt(lightpos[0],lightpos[1],lightpos[2],objpos[0],objpos[1],objpos[2],0.0,1.0,0.0)
    objtransform()
    view_mat = glGetFloatv(GL_MODELVIEW_MATRIX)
    glLibPopView()
    shader.pass_mat4("modelmatrix",view_mat)
    
    for index in range(2,2*len(posmaps)+2,2):
        shader.pass_texture(posmaps [index-2],index  )
        shader.pass_texture(normmaps[index-2],index+1)
    shader.pass_texture(GLLIB_CAUSTIC_POINT,1)
    ptsize = glGetFloatv(GL_POINT_SIZE)
    glPointSize(particlesize)
    glEnable(GL_POINT_SPRITE)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glDisable(GL_DEPTH_TEST)
    for colordata in particlecolordata:
        shader.pass_vec3("light_splat_color",colordata[0])
        shader.pass_float("eta",colordata[1])
        causticgrid.draw()
    glEnable(GL_DEPTH_TEST)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDisable(GL_POINT_SPRITE)
    glPointSize(ptsize)
    glLibUseShader(None)
    if fbo != None:
        fbo.disable()
        causticmap = fbo.get_texture(1)
    else:
        causticmap = glLibSceneToTexture(lightview.rect,causticmap,GLLIB_RGB,filtering,precision=precision)
##        glLibScreenshot("caustics.png",rect=GLLIB_AUTO,type=GLLIB_RGB,framebuffer=0,overwrite=True)
    return causticmap
def glLibAccumFilter(scenebuffer,view2d,filter):
    glLibUseShader(None)
    glDisable(GL_LIGHTING)
    glLoadIdentity()

    view2d.set_view()
    size = view2d.rect[2:]
    filtersize = [len(filter[0]),len(filter)]
    total = float(sum([sum(row) for row in filter]))
    if total == 0.0: total = 1.0

    glClear(GL_ACCUM_BUFFER_BIT)
    glLibSelectTexture(scenebuffer)
    
    xindex = 0
    for xjitter in range((-filtersize[0]//2)+1,(filtersize[0]//2)+1,1):
        yindex = 0
        for yjitter in range((-filtersize[1]//2)+1,(filtersize[1]//2)+1,1):
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
            glBegin(GL_QUADS)
            glTexCoord2f(0,0);glVertex2f(xjitter,        yjitter       )
            glTexCoord2f(1,0);glVertex2f(xjitter+size[0],yjitter       )
            glTexCoord2f(1,1);glVertex2f(xjitter+size[0],yjitter+size[1])
            glTexCoord2f(0,1);glVertex2f(xjitter,        yjitter+size[1])
            glEnd()
            glAccum(GL_ACCUM,filter[yindex][xindex]/total)
            yindex += 1
        xindex += 1
    glAccum(GL_RETURN,1.0)
    glEnable(GL_LIGHTING)
gllib_textures = {}
def glLibAccumSeparableFilter(scenebuffer,view2d,filter,filtersize):
    glLibUseShader(None)
    glDisable(GL_LIGHTING)
    glLoadIdentity()

    view2d.set_view()
    size = list(view2d.rect[2:])
    if filter == GLLIB_GAUSS:
        minx = (-filtersize[0]//2)+1
        maxx = (filtersize[0]//2)+1
        zmax = 2.9653100000109589
        filter = [(1.0/(2.0*pi))*(e**(-((float(2.0*x*zmax)/filtersize[0])**2)/2.0)) for x in range(minx,maxx,1)]
        filter = [filter,filter]
##    elif filter == GLLIB_BLOOM:
##        original_rect = list(view2d.rect)
##        texture_sizes = []
##        for texture_pass in range(filtersize[2]):
##            glLibAccumSeparableFilter(scenebuffer,view2d,GLLIB_GAUSS,filtersize[:2])
##            string_rect = str(view2d.rect)
##            if string_rect not in gllib_textures.keys():
##                gllib_textures[string_rect] = glLibSceneToTexture(view2d.rect,None,scenebuffer.format,scenebuffer.filtering,scenebuffer.mipmapping)
##            else:
##                gllib_textures[string_rect] = glLibSceneToTexture(view2d.rect,gllib_textures[string_rect])
##            texture_sizes.append(string_rect)
##            view2d.rect[2] = rndint(filtersize[3]*view2d.rect[2])
##            view2d.rect[3] = rndint(filtersize[3]*view2d.rect[3])
##        view2d.rect = list(original_rect)
##        view2d.set_view()
##        glClear(GL_ACCUM_BUFFER_BIT)
##        glDisable(GL_LIGHTING)
##        for texture_size in texture_sizes:
##            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
##            glLibSelectTexture(gllib_textures[texture_size])
##            glBegin(GL_QUADS)
##            glTexCoord2f(0,0);glVertex2f(0,      0      )
##            glTexCoord2f(1,0);glVertex2f(size[0],0      )
##            glTexCoord2f(1,1);glVertex2f(size[0],size[1])
##            glTexCoord2f(0,1);glVertex2f(0,      size[1])
##            glEnd()
##            glAccum(GL_ACCUM,1.0/filtersize[2])
##        glAccum(GL_RETURN,1.0)
##        glEnable(GL_LIGHTING)
##        return
    totals = list(map(float,[sum(filter[0]),sum(filter[1])]))
    
    glClear(GL_ACCUM_BUFFER_BIT)
    glLibSelectTexture(scenebuffer)
    
    index = 0
    for xjitter in range((-filtersize[0]//2)+1,(filtersize[0]//2)+1,1):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glBegin(GL_QUADS)
        glTexCoord2f(0,0);glVertex2f(xjitter,        0      )
        glTexCoord2f(1,0);glVertex2f(xjitter+size[0],0      )
        glTexCoord2f(1,1);glVertex2f(xjitter+size[0],size[1])
        glTexCoord2f(0,1);glVertex2f(xjitter,        size[1])
        glEnd()
        glAccum(GL_ACCUM,filter[0][index]/totals[0])
        index += 1
    glAccum(GL_RETURN,1.0)
    scenebuffer = glLibSceneToTexture(view2d.rect,scenebuffer)
    glLibSelectTexture(scenebuffer)
    glClear(GL_ACCUM_BUFFER_BIT)
    index = 0
    for yjitter in range((-filtersize[1]//2)+1,(filtersize[1]//2)+1,1):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glBegin(GL_QUADS)
        glTexCoord2f(0,0);glVertex2f(0,      yjitter        )
        glTexCoord2f(1,0);glVertex2f(size[0],yjitter        )
        glTexCoord2f(1,1);glVertex2f(size[0],yjitter+size[1])
        glTexCoord2f(0,1);glVertex2f(0,      yjitter+size[1])
        glEnd()
        glAccum(GL_ACCUM,filter[1][index]/totals[1])
        index += 1
    glAccum(GL_RETURN,1.0)
    glEnable(GL_LIGHTING)
