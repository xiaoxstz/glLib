from glLibLocals import *
from glLibMath import rndint
from glLibTexturing import *
class glLibFBO:
    def __init__(self,size,depthsize=8,stencilsize=0,samples=1):
        #http://www.gamedev.net/topic/457899-using-stencil-buffer-at-fbo/
        self.size = list(map(rndint,size))
        self.dimensions = len(self.size)
        if self.dimensions == 3:
            self.select_layer = self.glLibInternal_select_layer
        
        self.textures = {}
        self.render_buffers = {}
        self.currently_using = []
        
        self.framebuffer = glGenFramebuffersEXT(1)
        self.renderbuffer = glGenRenderbuffersEXT(1)
        
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT,self.framebuffer)
        glBindRenderbufferEXT(GL_RENDERBUFFER_EXT,self.renderbuffer)
        if stencilsize == 0:
            if   depthsize ==  8: depth = GL_DEPTH_COMPONENT
            elif depthsize == 16: depth = GL_DEPTH_COMPONENT16
            elif depthsize == 24: depth = GL_DEPTH_COMPONENT24
            elif depthsize == 32: depth = GL_DEPTH_COMPONENT32
            else:
                raise glLibError("Unsupported depth size!")
            if samples==1:
                glRenderbufferStorageEXT           (GL_RENDERBUFFER_EXT,        depth,self.size[0],self.size[1])
            else:
                glRenderbufferStorageMultisampleEXT(GL_RENDERBUFFER_EXT,samples,depth,self.size[0],self.size[1])
    ##        print GL_MAX_SAMPLES_EXT
            glFramebufferRenderbufferEXT(GL_FRAMEBUFFER_EXT,GL_DEPTH_ATTACHMENT_EXT,GL_RENDERBUFFER_EXT,self.renderbuffer)
        else:
            if not (stencilsize == 8 and depthsize == 24):
                raise glLibError("Unsupported stencil / depth sizes!  Try 8 and 24.")
            glRenderbufferStorageEXT(GL_RENDERBUFFER_EXT,GL_DEPTH_STENCIL_EXT,self.size[0],self.size[1])
            glFramebufferRenderbufferEXT(GL_FRAMEBUFFER_EXT,  GL_DEPTH_ATTACHMENT_EXT,GL_RENDERBUFFER_EXT,self.renderbuffer)
            glFramebufferRenderbufferEXT(GL_FRAMEBUFFER_EXT,GL_STENCIL_ATTACHMENT_EXT,GL_RENDERBUFFER_EXT,self.renderbuffer)
        glBindRenderbufferEXT(GL_RENDERBUFFER_EXT,0)
        
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT,0)

        self.check_status()
        if self.status != "GL_FRAMEBUFFER_COMPLETE_EXT":
            raise glLibError("Error: FBO unavailable ("+self.status+")")
    def __del__(self):
        glDeleteRenderbuffersEXT(1,[self.renderbuffer])
        glDeleteFramebuffersEXT(1,[self.framebuffer])
    def add_render_target(self,number,type=GLLIB_RGB,filtering=False,mipmapping=False,precision=8):
        #data,rect,format,filtering=False,mipmapping=False,colorkey=None,precision=8
        if   self.dimensions == 2: newtexture = glLibTexture2D(None,[0,0,self.size[0],self.size[1]],type,filtering,mipmapping,None,precision)
        elif self.dimensions == 3:
            if type == GLLIB_RGB: add = 3
            elif type == GLLIB_RGBA: add = 4
            else: raise glLibError("Error: type not allowed for 3D FBOs")
            newtexture = glLibTexture3D(np.zeros(self.size+[add]),[self.size[0],self.size[1],self.size[2]],type,filtering,mipmapping,None,precision)
        if mipmapping != False:
##            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
##            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
####            glTexParameteri(GL_TEXTURE_2D,GL_GENERATE_MIPMAP,GL_TRUE)
##            glGenerateMipmapEXT(GL_TEXTURE_2D)
            self.mipmapping = True
        if type == GLLIB_DEPTH: attachment = GL_DEPTH_ATTACHMENT_EXT
        else:                   attachment = GL_COLOR_ATTACHMENT0_EXT+number
        self.textures[number] = newtexture
        if attachment == GL_DEPTH_ATTACHMENT_EXT: self.render_buffers[number] = GL_NONE
        else:                                     self.render_buffers[number] = attachment
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT,self.framebuffer)
        if   self.dimensions == 2: glFramebufferTexture2DEXT(GL_FRAMEBUFFER_EXT,attachment,GL_TEXTURE_2D,self.textures[number].texture,0)
        elif self.dimensions == 3:
            for z in xrange(self.size[2]):
                glFramebufferTexture3DEXT(GL_FRAMEBUFFER_EXT,attachment,GL_TEXTURE_3D,self.textures[number].texture,0,z)
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT,0)
    def set_render_target(self,number,newtexture):
        try:
            del self.textures[number]
            del self.render_buffers[number]
        except:pass
        self.textures[number] = newtexture
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT,self.framebuffer)
        if   self.dimensions == 2: glFramebufferTexture2DEXT(GL_FRAMEBUFFER_EXT,GL_COLOR_ATTACHMENT0_EXT+number,GL_TEXTURE_2D,self.textures[number].texture,0)
        elif self.dimensions == 3:
            for z in xrange(self.size[2]):
                glFramebufferTexture3DEXT(GL_FRAMEBUFFER_EXT,GL_COLOR_ATTACHMENT0_EXT+number,GL_TEXTURE_3D,self.textures[number].texture,0,z)
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT,0)
    def remove_render_target(self,number):
        del self.textures[number]
        del self.render_buffers[number]
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT,self.framebuffer)
        if   self.dimensions == 2: glFramebufferTexture2DEXT(GL_FRAMEBUFFER_EXT,GL_COLOR_ATTACHMENT0_EXT+number,GL_TEXTURE_2D,0,0)
        elif self.dimensions == 3:
            for z in xrange(self.size[2]):
                glFramebufferTexture3DEXT(GL_FRAMEBUFFER_EXT,GL_COLOR_ATTACHMENT0_EXT+number,GL_TEXTURE_3D,0,0,z)
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT,0)
    def check_status(self):
        def glLibInternal_status_parse(status):
            if   status == GL_FRAMEBUFFER_COMPLETE_EXT:
                status =  "GL_FRAMEBUFFER_COMPLETE_EXT"
            elif status == GL_FRAMEBUFFER_UNSUPPORTED_EXT:
                status =  "GL_FRAMEBUFFER_UNSUPPORTED_EXT"
            elif status == GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT_EXT:
                status =  "GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT_EXT"
            elif status == GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT_EXT:
                status =  "GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT_EXT"
            elif status == GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS_EXT:
                status =  "GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS_EXT"
            elif status == GL_FRAMEBUFFER_INCOMPLETE_DUPLICATE_ATTACHMENT_EXT:
                status =  "GL_FRAMEBUFFER_INCOMPLETE_DUPLICATE_ATTACHMENT_EXT"
            elif status == GL_FRAMEBUFFER_INCOMPLETE_FORMATS_EXT:
                status =  "GL_FRAMEBUFFER_INCOMPLETE_FORMATS_EXT"
            elif status == GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER_EXT:
                status =  "GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER_EXT"
            elif status == GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER_EXT:
                status =  "GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER_EXT"
            elif status == GL_FRAMEBUFFER_BINDING_EXT:
                status =  "GL_FRAMEBUFFER_BINDING_EXT"
##            elif status == GL_FRAMEBUFFER_STATUS_ERROR_EXT:
##                status =  "GL_FRAMEBUFFER_STATUS_ERROR_EXT"
            if GLLIB_MULTISAMPLE_FRAMEBUFFERS_AVAILABLE:
                if  status == GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE_EXT:
                    status = "GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE_EXT"
            return status
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT,self.framebuffer)
        if   self.dimensions == 2:
            self.enable(GLLIB_ALL)
            status = glCheckFramebufferStatusEXT(GL_FRAMEBUFFER_EXT)
            self.disable()
            self.status = glLibInternal_status_parse(status)
        elif self.dimensions == 3:
            self.enable(GLLIB_ALL)
            for z in xrange(self.size[2]):
                self.select_layer(z)
                status = glCheckFramebufferStatusEXT(GL_FRAMEBUFFER_EXT)
                self.status = glLibInternal_status_parse(status)
                if self.status != "GL_FRAMEBUFFER_COMPLETE_EXT":
                    self.status += " on (at least) layer " + str(z)
                    break
            self.disable()
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT,0)
        return status #GL_FRAMEBUFFER_COMPLETE_EXT
    def enable(self,key_list):
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT,self.framebuffer)
        if key_list == GLLIB_ALL: key_list = self.textures.keys()
        array = []
        for key in key_list:
            array.append(self.render_buffers[key])
        self.currently_using = list(key_list)
        glDrawBuffers(len(key_list),np.array(array))
##        glGenerateMipmapEXT(GL_TEXTURE_2D)
    def glLibInternal_select_layer(self,layer):
        for key in self.currently_using:
            glFramebufferTexture3DEXT(GL_FRAMEBUFFER_EXT,GL_COLOR_ATTACHMENT0_EXT+key,GL_TEXTURE_3D,self.textures[key].texture,0,layer)
    def disable(self):
        self.currently_using = []
        glDrawBuffers(1,np.array([GL_COLOR_ATTACHMENT0_EXT]))
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT,0)
    def get_texture(self,rendertarget):
        return self.textures[rendertarget]
    def get_textures(self):
        return list(self.textures.values())
