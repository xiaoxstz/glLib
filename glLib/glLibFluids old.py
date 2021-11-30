from glLibLocals import *
from glLibFBO import *
from glLibMath import *
from glLibMisc import *
from glLibObjects import *
from glLibView import *
from glLibShader import *
class glLibFluidGasGPU:
    def __init__(self,res):
        #heavily based on http://http.developer.nvidia.com/GPUGems/gpugems_ch38.html
        
        self.res = list(res)
        self.diff = 0.0
        self.visc = 0.0

        self.new_forces = []
        self.new_densities = []

        self.view2D = glLibView2D((0,0,self.res[0],self.res[1]))

        self.precis = 32

        self.advection_fbo1 = glLibFBO((self.res[0],self.res[1]))
        self.advection_fbo2 = glLibFBO((self.res[0],self.res[1]))
        self.advection_fbo1.add_render_target(1,GLLIB_RGB,GLLIB_FILTER,precision=self.precis)
        self.advection_fbo2.add_render_target(1,GLLIB_RGB,GLLIB_FILTER,precision=self.precis)
        
        self.diffusion_jacobi_fbo1 = glLibFBO((self.res[0],self.res[1]))
        self.diffusion_jacobi_fbo2 = glLibFBO((self.res[0],self.res[1]))
        self.diffusion_jacobi_fbo1.add_render_target(1,GLLIB_RGB,GLLIB_FILTER,precision=self.precis)
        self.diffusion_jacobi_fbo2.add_render_target(1,GLLIB_RGB,GLLIB_FILTER,precision=self.precis)
        
        self.add_fbo1 = glLibFBO((self.res[0],self.res[1]))
        self.add_fbo2 = glLibFBO((self.res[0],self.res[1]))
        self.add_fbo1.add_render_target(1,GLLIB_RGB,GLLIB_FILTER,precision=self.precis)
        self.add_fbo2.add_render_target(1,GLLIB_RGB,GLLIB_FILTER,precision=self.precis)
        
        self.pressure_fbo = glLibFBO((self.res[0],self.res[1]))
        self.pressure_fbo.add_render_target(1,GLLIB_RGB,GLLIB_FILTER,precision=self.precis)

        self.pressure_jacobi_fbo1 = glLibFBO((self.res[0],self.res[1]))
        self.pressure_jacobi_fbo2 = glLibFBO((self.res[0],self.res[1]))
        self.pressure_jacobi_fbo1.add_render_target(1,GLLIB_RGB,GLLIB_FILTER,precision=self.precis)
        self.pressure_jacobi_fbo2.add_render_target(1,GLLIB_RGB,GLLIB_FILTER,precision=self.precis)
        
        self.spressure_fbo = glLibFBO((self.res[0],self.res[1]))
        self.spressure_fbo.add_render_target(1,GLLIB_RGB,GLLIB_FILTER,precision=self.precis)

        self.advection_ping_pong = 1
        self.add_ping_pong = 1
        self.diffusion_jacobi_ping_pong = 1
        self.pressure_jacobi_ping_pong = 1

        zero_value = np.empty((self.res[0],self.res[1],3))
        zero_value.fill(127.5)
        zero_value = pygame.surfarray.make_surface(zero_value)
        
        self.velocity_tex = glLibTexture2D(zero_value,GLLIB_ALL,GLLIB_RGB,GLLIB_FILTER,precision=32)

        self.gas_tex = glLibTexture2D(pygame.Surface(self.res),GLLIB_ALL,GLLIB_RGB,GLLIB_FILTER,precision=32)

        self.advection_shader = glLibShader()
        self.advection_shader.user_variables("""
        uniform float dt;
        const vec2 gridsize = vec2("""+str(self.res[0])+","+str(self.res[1])+""");
        const vec2 griddelta = 1.0/gridsize;""")
        self.advection_shader.render_equation("""
        //follow the velocity field "back in time", then interpolate and write to the output fragment
        //tex2D_1 contains the velocities; tex2D_2 contains the quantity to be advected
        vec2 pos = uv - dt * griddelta * vec3(texture2D(tex2D_1,uv).rgb-vec3(0.5)).rg;
        color.rgb = texture2D(tex2D_2,pos).rgb;""")
        print "Advection Shader"
        print self.advection_shader.compile()

        self.jacobi_shader = glLibShader()
        self.jacobi_shader.user_variables("""
        uniform float iterations;
        uniform float dt;
        const vec2 gridsize = vec2("""+str(self.res[0])+","+str(self.res[1])+""");
        const vec2 griddelta = 1.0/gridsize;
        float alpha = griddelta.x*griddelta.y/(iterations*dt);
        float rBeta = 1.0/(4.0+alpha);""")
        self.jacobi_shader.render_equation("""
        //Ax = b; tex2D_1 contains the x vector; tex2D_2 contains the b vector
        
        //left, right, bottom, and top x samples
        vec4 xL = texture2D(tex2D_1,uv-vec2(griddelta.x,0));
        vec4 xR = texture2D(tex2D_1,uv+vec2(griddelta.x,0));
        vec4 xB = texture2D(tex2D_1,uv-vec2(0,griddelta.y));
        vec4 xT = texture2D(tex2D_1,uv+vec2(0,griddelta.y));
        //b sample, from center
        vec4 bC = texture2D(tex2D_2,uv);

        // evaluate Jacobi iteration
        color = (xL + xR + xB + xT + alpha * bC) * rBeta;""")
        print "Jacobi Shader"
        print self.jacobi_shader.compile()

        self.divergence_shader = glLibShader()
        self.divergence_shader.user_variables("""
        uniform float iterations;
        uniform float dt;
        const vec2 gridsize = vec2("""+str(self.res[0])+","+str(self.res[1])+""");
        const vec2 griddelta = 1.0/gridsize;
        const float halfrdx = 0.5*griddelta.x;""")
        self.divergence_shader.render_equation("""
        //tex2D_1 contains the w vector field
        vec4 wL = texture2D(tex2D_1,uv-vec2(griddelta.x,0.0));
        vec4 wR = texture2D(tex2D_1,uv+vec2(griddelta.x,0.0));
        vec4 wB = texture2D(tex2D_1,uv-vec2(0.0,griddelta.y));
        vec4 wT = texture2D(tex2D_1,uv+vec2(0.0,griddelta.y));

        color.rgb = vec3(  halfrdx * ((wR.x-wL.x)+(wT.y-wB.y))  );
        color.rgb += 0.5;""")
        print "Divergence Shader"
        print self.divergence_shader.compile()

        self.gradient_subtract_shader = glLibShader()
        self.gradient_subtract_shader.user_variables("""
        const vec2 gridsize = vec2("""+str(self.res[0])+","+str(self.res[1])+""");
        const vec2 griddelta = 1.0/gridsize;
        const float halfrdx = 0.5*griddelta.x;""")
        self.gradient_subtract_shader.render_equation("""
        //tex2D_1 contains the pressure; tex2D_2 contains the velocity
        float pL = texture2D(tex2D_1,uv-vec2(griddelta.x,0.0)).r;
        float pR = texture2D(tex2D_1,uv+vec2(griddelta.x,0.0)).r;
        float pB = texture2D(tex2D_1,uv-vec2(0.0,griddelta.y)).r;
        float pT = texture2D(tex2D_1,uv+vec2(0.0,griddelta.y)).r;

        color.rgb = texture2D(tex2D_2,uv).rgb;
        color.rg -= halfrdx * vec2(pR-pL,pT-pB);""")
        print "Gradient Subtract Shader"
        print self.gradient_subtract_shader.compile()

        self.add_shader = glLibShader()
        self.add_shader.user_variables("uniform vec3 quantity;")
        self.add_shader.render_equation("""
        color.rgb = texture2D(tex2D_1,uv).rgb + quantity;""")
        print "Add Shader"
        print self.add_shader.compile()
    def glLibInternal_advect(self,velocity,quantity,dt):
        glLibUseShader(self.advection_shader)
        
        if self.advection_ping_pong == 1: self.advection_fbo1.enable([1])
        else:                             self.advection_fbo2.enable([1])
        self.view2D.set_view()
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
        
        self.advection_shader.pass_float("dt",dt)
        self.advection_shader.pass_texture(velocity,1)
        self.advection_shader.pass_texture(quantity,2)
        glLibDrawScreenQuad(texture=True)
        
        if self.advection_ping_pong == 1: self.advection_fbo1.disable(); texture = self.advection_fbo1.get_texture(1)
        else:                             self.advection_fbo2.disable(); texture = self.advection_fbo2.get_texture(1)
        self.advection_ping_pong = 3 - self.advection_ping_pong
        return texture
    def glLibInternal_diffuse(self,n,dt):
        glLibUseShader(self.jacobi_shader)
        self.jacobi_shader.pass_float("iterations",n)
        self.jacobi_shader.pass_float("dt",dt)
        for jacobi_iter in xrange(n):
            if self.diffusion_jacobi_ping_pong == 1: self.diffusion_jacobi_fbo1.enable([1])
            else:                                    self.diffusion_jacobi_fbo2.enable([1])
            self.view2D.set_view()
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
            self.jacobi_shader.pass_texture(self.velocity_tex,1) #x vector
            self.jacobi_shader.pass_texture(self.velocity_tex,2) #b vector
            glLibDrawScreenQuad(texture=True)
            if self.diffusion_jacobi_ping_pong == 1: self.diffusion_jacobi_fbo1.disable(); self.velocity_tex = self.diffusion_jacobi_fbo1.get_texture(1)
            else:                                    self.diffusion_jacobi_fbo2.disable(); self.velocity_tex = self.diffusion_jacobi_fbo2.get_texture(1)
            self.diffusion_jacobi_ping_pong = 3 - self.diffusion_jacobi_ping_pong
    def glLibInternal_add(self,data_tex,quantities):
        glLibUseShader(self.add_shader)
        
        if self.add_ping_pong == 1: self.add_fbo1.enable([1])
        else:                       self.add_fbo2.enable([1])
        self.view2D.set_view()
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
        
        self.add_shader.pass_texture(data_tex,1)
        self.add_shader.pass_vec3("quantity",[0.0,0.0,0.0])
        glLibDrawScreenQuad(texture=True)
        for quantity in quantities:
            self.add_shader.pass_vec3("quantity",quantity[1])
            glPointSize(10)
            glBegin(GL_POINTS)
            glVertex3f(quantity[0][0],quantity[0][1],0)
            glEnd()
        
        if self.add_ping_pong == 1: self.add_fbo1.disable(); texture = self.add_fbo1.get_texture(1)
        else:                       self.add_fbo2.disable(); texture = self.add_fbo2.get_texture(1)
        self.add_ping_pong = 3 - self.add_ping_pong
        return texture
    def glLibInternal_computepressure(self,velocity,n,dt):
        glLibUseShader(self.divergence_shader)
        
        self.pressure_fbo.enable([1])
        self.view2D.set_view()
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
        
        self.divergence_shader.pass_texture(velocity,1)
        glLibDrawScreenQuad(texture=True)
        
        self.pressure_fbo.disable()
        self.pressure_tex = self.pressure_fbo.get_texture(1)

        glLibUseShader(self.jacobi_shader)
        self.jacobi_shader.pass_float("iterations",n)
        self.jacobi_shader.pass_float("dt",dt)
        for jacobi_iter in xrange(n):
            if self.pressure_jacobi_ping_pong == 1: self.pressure_jacobi_fbo1.enable([1])
            else:                                   self.pressure_jacobi_fbo2.enable([1])
            self.view2D.set_view()
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
            self.jacobi_shader.pass_texture(self.velocity_tex,1) #x vector
            self.jacobi_shader.pass_texture(self.velocity_tex,2) #b vector
            glLibDrawScreenQuad(texture=True)
            if self.pressure_jacobi_ping_pong == 1: self.pressure_jacobi_fbo1.disable(); self.velocity_tex = self.pressure_jacobi_fbo1.get_texture(1)
            else:                                   self.pressure_jacobi_fbo2.disable(); self.velocity_tex = self.pressure_jacobi_fbo2.get_texture(1)
            self.pressure_jacobi_ping_pong = 3 - self.pressure_jacobi_ping_pong
        return self.pressure_fbo.get_texture(1)
    def glLibInternal_subtractpressuregradient(self,velocity,pressure):
        glLibUseShader(self.gradient_subtract_shader)
        
        self.spressure_fbo.enable([1])
        self.view2D.set_view()
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
        
        self.gradient_subtract_shader.pass_texture(pressure,1)
        self.gradient_subtract_shader.pass_texture(velocity,2)
        glLibDrawScreenQuad(texture=True)
        
        self.pressure_fbo.disable()
        return self.spressure_fbo.get_texture(1)
    def add_density_at(self,coord,density):
        self.new_densities.append([coord,density])
    def add_force_at(self,coord,force):
        self.new_forces.append([coord,force])
    def reset(self):pass
    def step(self,dt):
        glLibPushView()
        glDepthFunc(GL_LEQUAL)
        
        #Apply the first 3 operators in Equation 12.
        self.velocity_tex = self.glLibInternal_add(self.velocity_tex,self.new_forces); self.new_forces = []
        self.gas_tex      = self.glLibInternal_add(self.gas_tex,self.new_densities); self.new_densities = []
        
        self.velocity_tex = self.glLibInternal_advect(self.velocity_tex,self.velocity_tex,dt)
        self.gas_tex = self.glLibInternal_advect(self.velocity_tex,self.gas_tex,dt)
        
##        self.glLibInternal_diffuse(20,dt)
        #Now apply the projection operator to the result.
        self.glLibInternal_computepressure(self.velocity_tex,60,dt)
        self.velocity_tex = self.glLibInternal_subtractpressuregradient(self.velocity_tex,self.pressure_tex)
        
        glDepthFunc(GL_LESS)
        glLibPopView()
        glLibUseShader(None)
    def draw(self):
        glDisable(GL_LIGHTING)
        glLibSelectTexture(self.gas_tex)
        glBegin(GL_QUADS)
        glTexCoord2f(0,0); glVertex3f(-0.5,0,-0.5)
        glTexCoord2f(1,0); glVertex3f( 0.5,0,-0.5)
        glTexCoord2f(1,1); glVertex3f( 0.5,0, 0.5)
        glTexCoord2f(0,1); glVertex3f(-0.5,0, 0.5)
        glEnd()
        glEnable(GL_LIGHTING)
        
        glLibPushView()
        glEnable(GL_SCISSOR_TEST)
        glDisable(GL_LIGHTING)

        if hasattr(self,"gas_tex"):
            glLibView2D((0+2,2,self.res[0],self.res[1])).set_view()
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
            glLibDrawScreenQuad(texture=self.gas_tex)

        if hasattr(self,"velocity_tex"):
            glLibView2D((128+4,2,self.res[0],self.res[1])).set_view()
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
            glLibDrawScreenQuad(texture=self.velocity_tex)

        if hasattr(self,"pressure_tex"):
            glLibView2D((256+6,2,self.res[0],self.res[1])).set_view()
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
            glLibDrawScreenQuad(texture=self.pressure_tex)
        
        glEnable(GL_LIGHTING)
        glDisable(GL_SCISSOR_TEST)
        glLibPopView()
#===============================================================================================================
class glLibFluidGasCPU:
    def __init__(self,res):
        self.res = list(res)
        self.N = res[0]
        self.size = tuple([self.N+2,self.N+2])

        self.diff = 0.0#01
        self.visc = 0.0#01

        #precision
        self.precision = np.float32
        #velocity
        self.u      = np.zeros(self.size,self.precision)
        self.u_prev = np.zeros(self.size,self.precision)
        self.v      = np.zeros(self.size,self.precision) 
        self.v_prev = np.zeros(self.size,self.precision)
        #density
        self.dens      = np.zeros(self.size,self.precision)
        self.dens_prev = np.zeros(self.size,self.precision)
        self.reset()
    def add_density_at(self,coord,density):
        self.dens_prev[coord[0],coord[1]] += density
    def add_force_at(self,coord,force):
        self.u[coord[0],coord[1]] += force[0]
        self.v[coord[0],coord[1]] += force[1]
    def step(self,dt):
        def set_bnd(b, x):
            for i in range(1,self.N+1):
                if b == 1: x[0,i] = -x[1,i]
                else:      x[0,i] =  x[1,i]
                if b == 1: x[self.N+1,i] = -x[self.N,i]
                else:      x[self.N+1,i] =  x[self.N,i]
                if b == 2: x[i,0] = -x[i,1]
                else:      x[i,0] =  x[i,1]
                if b == 2: x[i,self.N+1] = -x[i,self.N]
                else:      x[i,self.N+1] =  x[i,self.N]
            x[0,0] = 0.5*(x[1,0]+x[0,1])
            x[0,self.N+1] = 0.5*(x[1,self.N+1]+x[0,self.N])
            x[self.N+1,0] = 0.5*(x[self.N,0]+x[self.N+1,1])
            x[self.N+1,self.N+1] = 0.5*(x[self.N,self.N+1]+x[self.N+1,self.N])
            
        def lin_solve(b,x,x0,a,c):
            for k in range(0,20):
                x[1:self.size[0]-1,1:self.size[1]-1] = (x0[1:self.size[0]-1,1:self.size[1]-1] + a*(x[0:self.N,  1:self.N+1]+\
                                                                                                   x[2:self.N+2,1:self.N+1]+\
                                                                                                   x[1:self.N+1,0:self.N  ]+\
                                                                                                   x[1:self.N+1,2:self.N+2]))/c
                set_bnd(b, x)
                
        def diffuse(b,x,x0,diff):
            a = dt*diff*self.N*self.N
            lin_solve(b,x,x0,a,1+4*a)
            
        def advect(b,d,d0,u,v):
            dt0 = dt*self.N;
            for i in range(1, self.N+1):
                for j in range(1, self.N+1):
                    x = i-dt0*u[i,j]; y = j-dt0*v[i,j]
                    if x<0.5: x=0.5
                    if x>self.N+0.5: x=self.N+0.5
                    i0 = int(x); i1 = i0+1
                    if y<0.5: y=0.5
                    if y>self.N+0.5: y=self.N+0.5
                    j0 = int(y); j1 = j0+1
                    s1 = x-i0; s0 = 1-s1; t1 = y-j0; t0 = 1-t1
                    d[i,j] = s0*(t0*d0[i0,j0]+t1*d0[i0,j1])+s1*(t0*d0[i1,j0]+t1*d0[i1,j1])
            set_bnd(b, d)
            
        def project():
            h = 1.0/self.N
            self.v_prev[1:self.N+1,1:self.N+1] = -0.5*h*(self.u[2:self.N+2,1:self.N+1]-self.u[0:self.N,1:self.N+1]+self.v[1:self.N+1,2:self.N+2]-self.v[1:self.N+1,0:self.N])
            self.u_prev[1:self.N+1,1:self.N+1] = 0
            set_bnd(0, self.v_prev)
            set_bnd(0, self.u_prev)
            lin_solve(0, self.u_prev, self.v_prev, 1, 4)
            self.u[1:self.N+1,1:self.N+1] -= 0.5*(self.u_prev[2:self.N+2,1:self.N+1]-self.u_prev[0:self.N,1:self.N+1])/h # ??? not in the paper /h
            self.v[1:self.N+1,1:self.N+1] -= 0.5*(self.u_prev[1:self.N+1,2:self.N+2]-self.u_prev[1:self.N+1,0:self.N])/h # ??? not in the paper /h
            set_bnd(1, self.u)
            set_bnd(2, self.v)
            
        #Velocity step
        self.u += dt*self.u_prev
        self.v += dt*self.v_prev
        
        self.u_prev, self.u = self.u, self.u_prev # swap
        self.v_prev, self.v = self.v, self.v_prev # swap
        
        diffuse(1, self.u, self.u_prev, self.visc)
        diffuse(2, self.v, self.v_prev, self.visc)
        
        project()
        
        self.u_prev, self.u = self.u, self.u_prev # swap
        self.v_prev, self.v = self.v, self.v_prev # swap
        
        advect(1, self.u, self.u_prev, self.u_prev, self.v_prev)
        advect(2, self.v, self.v_prev, self.u_prev, self.v_prev)
        
        project()
        
        #Density step
        self.dens += dt*self.dens_prev
        
        self.dens_prev,self.dens = self.dens,self.dens_prev # swap
        
        diffuse(0, self.dens, self.dens_prev, self.diff)
        
        self.dens_prev,self.dens = self.dens,self.dens_prev # swap
        
        advect(0, self.dens, self.dens_prev, self.u, self.v)
        
        #Resets
        self.dens_prev[:,:] = 0.0
        
        self.u_prev[:,:] = 0.0
        self.v_prev[:,:] = 0.0
    def reset(self):
        self.u[:,:] = 0.0
        self.v[:,:] = 0.0
        self.u_prev[:,:] = 0.0
        self.v_prev[:,:] = 0.0
        
        self.dens[:,:] = 0.0
        self.dens_prev[:,:] = 0.0
    def draw(self):
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        h = 1.0/self.N
        glBegin(GL_QUADS)
        for i in range(0,self.N+1,1):
            x = (i-0.5)*h
            for j in range(0,self.N+1,1):
                y = (j-0.5)*h
                d00 = self.dens[i,j]
                d01 = self.dens[i,j+1]
                d10 = self.dens[i+1,j]
                d11 = self.dens[i+1,j+1]

                glColor3f(d00, d00, d00); glVertex3f(x, 0, y)
                glColor3f(d10, d10, d10); glVertex3f(x+h, 0, y)
                glColor3f(d11, d11, d11); glVertex3f(x+h, 0, y+h)
                glColor3f(d01, d01, d01); glVertex3f(x, 0, y+h)
        glEnd()
        glColor3f(1,1,1)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)
