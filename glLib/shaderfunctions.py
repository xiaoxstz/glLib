def glLibInternal_get_parallaxmap_funcs(uvtrans):
    string = ""
    if "parallaxmap" in uvtrans:
        string += """
        vec2 parallaxmap(sampler2D heightmap, vec2 texcoords, float scale, bool flip){
            float fDepth = 0.0;
            vec2 vHalfOffset = vec2(0.0,0.0);
            int i = 0;
            vec2 eyevec = vec2(dot(vVertex,t),dot(vVertex,b));
            if (flip){while (i < 3){
                fDepth= fDepth+(    texture2D(heightmap,texcoords+vHalfOffset).r) *0.5;
                vHalfOffset=normalize(eyevec).xy*fDepth*scale;
                i+=1;
            }}
            else     {while (i < 3){
                fDepth=(fDepth+(1.0-texture2D(heightmap,texcoords+vHalfOffset).r))*0.5;
                vHalfOffset=normalize(eyevec).xy*fDepth*scale;
                i+=1;
            }}
            return vHalfOffset;
        }"""
    if "parallax_occulsionmap" in uvtrans:
        string += """
        vec2 parallax_occulsionmap(sampler2D heightmap, vec2 texcoords, float scale, bool flip, int linear_search_steps, int binary_search_steps) {
            scale = scale/10.0;
            vec2 eyevec = vec2(dot(vVertex,t),dot(vVertex,b));
            vec2 ds=eyevec.xy*scale,offset;
            float depth_step=1.0/float(linear_search_steps),size=depth_step,depth=0.0,best_depth=1.0;
            if (flip) {
                for (int i=0; i<linear_search_steps-1; i++){
                    depth += size;vec4 t = texture2D(heightmap,texcoords+(ds*depth));
                    if (best_depth>0.996) {
                        if (depth>=t.r){
                            best_depth=depth;
                }}}
                depth = best_depth;
                for (int i=0; i<binary_search_steps; i++){
                    size *= 0.5;vec4 t = texture2D(heightmap,texcoords+(ds*depth));
                    if (depth>=t.r) {
                        best_depth=depth;depth-=2.0*size;
                    }
                    depth += size;
                }}
            else {
                for (int i=0; i<linear_search_steps-1; i++){
                    depth += size;vec4 t = 1.0-texture2D(heightmap,texcoords+(ds*depth));
                    if (best_depth>0.996) {
                        if (depth>=t.r){best_depth=depth;
                }}}
                depth = best_depth;
                for (int i=0; i<binary_search_steps; i++){
                    size *= 0.5;vec4 t = 1.0-texture2D(heightmap,texcoords+(ds*depth));
                    if (depth>=t.r) {
                        best_depth=depth;depth-=2.0*size;
                    }
                    depth += size;
                }}
            offset = ds*best_depth;
            return offset;//return vec3(offset.x,offset.y,best_depth);
        }"""
        string += """
        vec2 parallax_occulsionmap2(sampler2D heightmap, vec2 texture_size, vec2 texcoords, float height_scalar, bool flipdepth, int steps_guide) {
            vec3 vertex_vector = normalize(vVertex);
            vec2 texture_space_vec = vec2(dot(vertex_vector,normalize(t)),dot(vertex_vector,normalize(b)));
            vec3 eyevec = normalize(vec3(texture_space_vec,-(1.0-length(texture_space_vec))));
            
            int steps = 10;//mix(steps_guide*2, steps_guide, dot(normal,E))
            
            float last_height = texture2D(heightmap,texcoords).r;
            if (last_height==1.0) { return vec2(0.0,0.0); }
            if (flipdepth) { discard; }
            float new_height = 0.0;
            
            vec3 volume_position = vec3(0.0,0.0,1.0);
            if (eyevec.z>=-0.01) {discard;return vec2(0.0,0.0);}
            float x_sc_length=0.0, y_sc_length=0.0, minlength=0.0;
            while (volume_position.z>new_height) {
                if (eyevec.x<0.0) { x_sc_length=(( ceil(volume_position.x)-1.0)-volume_position.x)/dot(eyevec,vec3(1.0,0.0,0.0)); }
                else              { x_sc_length=((floor(volume_position.x)+1.0)-volume_position.x)/dot(eyevec,vec3(1.0,0.0,0.0)); }
                if (eyevec.y<0.0) { y_sc_length=(( ceil(volume_position.y)-1.0)-volume_position.y)/dot(eyevec,vec3(0.0,1.0,0.0)); }
                else              { y_sc_length=((floor(volume_position.y)+1.0)-volume_position.y)/dot(eyevec,vec3(0.0,1.0,0.0)); }
                minlength = min(x_sc_length,y_sc_length);
                volume_position.xy += minlength*eyevec.xy;
                volume_position.z += height_scalar*minlength*eyevec.z;
                new_height = texture2D(heightmap,texcoords+(volume_position.xy/texture_size)).r;
                //if (length(volume_position.xz)>2.0) { discard;return vec2(0.0,0.0); }
            }
            
            vec2 offset = volume_position.xy/texture_size;
            return offset;
        }"""
    return string
def glLibInternal_get_subsurface_absorb_funcs(renderequation):
    string = ""
    if "absorb" in renderequation:
        if "absorb2_" in renderequation:
            string += """
            float absorb2_point(vec2 coord,float alpha,float near,float far) {
                float depth1=texture2D(tex2D_1,coord).r;float depth2=texture2D(tex2D_2,coord).r;
                depth1=depth_from_depthbuffer(depth1,near,far);depth2=depth_from_depthbuffer(depth2,near,far);
                float length = depth2-depth1;
                return clamp(pow(10.0,-alpha*length),0.0,1.0);
            }
            float absorb2_proj(vec4 depth_coord,float alpha,float near,float far) {
                float coord = depth_from_depthbuffer(depth_coord.p/depth_coord.q,near,far);
                float depth1=texture2DProj(tex2D_1,depth_coord).r;float depth2=texture2DProj(tex2D_2,depth_coord).r;
                depth1=depth_from_depthbuffer(depth1,near,far);depth2=depth_from_depthbuffer(depth2,near,far);
                float diff1=abs(coord-depth1);float diff2=abs(coord-depth2);
                float length = 0.0;
                if (diff2<diff1) { length = coord-depth1; }
                return clamp(pow(10.0,-alpha*length),0.0,1.0);
            }"""
        if "absorb4_" in renderequation:
            string += """
            float absorb4_point(vec2 coord,float alpha,float near,float far) {
                float depth1=texture2D(tex2D_1,coord).r;float depth2=texture2D(tex2D_2,coord).r;
                float depth3=texture2D(tex2D_3,coord).r;float depth4=texture2D(tex2D_4,coord).r;
                depth1=depth_from_depthbuffer(depth1,near,far);depth2=depth_from_depthbuffer(depth2,near,far);
                depth3=depth_from_depthbuffer(depth3,near,far);depth4=depth_from_depthbuffer(depth4,near,far);
                float length = (depth2-depth1)+(depth4-depth3);
                return clamp(pow(10.0,-alpha*length),0.0,1.0);
            }
            float absorb4_proj(vec4 projcoord,float alpha,float near,float far) {
                float coord = depth_from_depthbuffer(depth_coord.p/depth_coord.q,near,far);
                float depth1=texture2DProj(tex2D_1,depth_coord).r;float depth2=texture2DProj(tex2D_2,depth_coord).r;
                float depth3=texture2DProj(tex2D_3,depth_coord).r;float depth4=texture2DProj(tex2D_4,depth_coord).r;
                depth1=depth_from_depthbuffer(depth1,near,far);depth2=depth_from_depthbuffer(depth2,near,far);
                depth3=depth_from_depthbuffer(depth3,near,far);depth4=depth_from_depthbuffer(depth4,near,far);
                float diff1=abs(coord-depth1);float diff2=abs(coord-depth2);float diff3=abs(coord-depth3);float diff4=abs(coord-depth4);
                float length = 0.0;
                if ((diff2<diff4)&&(diff2<diff3)&&(diff2<diff1)) { length = coord-depth1; }
                if ((diff3<diff4)&&(diff3<diff2)&&(diff3<diff1)) { length = (depth2-depth1); }
                if ((diff4<diff3)&&(diff4<diff2)&&(diff4<diff1)) { length = (depth4-depth3)+(depth2-depth1); }
                return clamp(pow(10.0,-alpha*length),0.0,1.0);
            }"""
        if "absorb6_" in renderequation:
            string += """
            float absorb6_point(vec2 coord,float alpha,float near,float far) {
                float depth1=texture2D(tex2D_1,coord).r;float depth2=texture2D(tex2D_2,coord).r;
                float depth3=texture2D(tex2D_3,coord).r;float depth4=texture2D(tex2D_4,coord).r;
                float depth5=texture2D(tex2D_5,coord).r;float depth6=texture2D(tex2D_6,coord).r;
                depth1=depth_from_depthbuffer(depth1,near,far);depth2=depth_from_depthbuffer(depth2,near,far);
                depth3=depth_from_depthbuffer(depth3,near,far);depth4=depth_from_depthbuffer(depth4,near,far);
                depth5=depth_from_depthbuffer(depth5,near,far);depth6=depth_from_depthbuffer(depth6,near,far);
                float length = (depth2-depth1)+(depth4-depth3)+(depth6-depth5);
                return clamp(pow(10.0,-alpha*length),0.0,1.0);
            }
            float absorb6_proj(vec4 depth_coord,float alpha,float near,float far) {
                float coord = depth_from_depthbuffer(depth_coord.p/depth_coord.q,near,far);
                float depth1=texture2DProj(tex2D_1,depth_coord).r;float depth2=texture2DProj(tex2D_2,depth_coord).r;
                float depth3=texture2DProj(tex2D_3,depth_coord).r;float depth4=texture2DProj(tex2D_4,depth_coord).r;
                float depth5=texture2DProj(tex2D_5,depth_coord).r;float depth6=texture2DProj(tex2D_6,depth_coord).r;
                depth1=depth_from_depthbuffer(depth1,near,far);depth2=depth_from_depthbuffer(depth2,near,far);
                depth3=depth_from_depthbuffer(depth3,near,far);depth4=depth_from_depthbuffer(depth4,near,far);
                depth5=depth_from_depthbuffer(depth5,near,far);depth6=depth_from_depthbuffer(depth6,near,far);
                float diff1=abs(coord-depth1);float diff2=abs(coord-depth2);float diff3=abs(coord-depth3);float diff4=abs(coord-depth4);float diff5=abs(coord-depth5);float diff6=abs(coord-depth6);
                float length = 0.0;
                if ((diff2<diff6)&&(diff2<diff5)&&(diff2<diff4)&&(diff2<diff3)&&(diff2<diff1)) { length = coord-depth1; }
                if ((diff3<diff6)&&(diff3<diff5)&&(diff3<diff4)&&(diff3<diff2)&&(diff3<diff1)) { length = depth2-depth1; }
                if ((diff4<diff6)&&(diff4<diff5)&&(diff4<diff3)&&(diff4<diff2)&&(diff4<diff1)) { length = (depth4-depth3)+(depth2-depth1); }
                if ((diff5<diff6)&&(diff5<diff4)&&(diff5<diff3)&&(diff5<diff2)&&(diff5<diff1)) { length = (depth4-depth3)+(depth2-depth1); }
                if ((diff6<diff5)&&(diff6<diff4)&&(diff6<diff3)&&(diff6<diff2)&&(diff6<diff1)) { length = (depth6-depth5)+(depth4-depth3)+(depth2-depth1); }
                return clamp(pow(10.0,-alpha*length),0.0,1.0);
            }"""
        if "absorb8_" in renderequation:
            string += """
            float absorb8_point(vec2 coord,float alpha,float near,float far) {
                float depth1=texture2D(tex2D_1,coord).r;float depth2=texture2D(tex2D_2,coord).r;
                float depth3=texture2D(tex2D_3,coord).r;float depth4=texture2D(tex2D_4,coord).r;
                float depth5=texture2D(tex2D_5,coord).r;float depth6=texture2D(tex2D_6,coord).r;
                float depth7=texture2D(tex2D_7,coord).r;float depth8=texture2D(tex2D_8,coord).r;
                depth1=depth_from_depthbuffer(depth1,near,far);depth2=depth_from_depthbuffer(depth2,near,far);
                depth3=depth_from_depthbuffer(depth3,near,far);depth4=depth_from_depthbuffer(depth4,near,far);
                depth5=depth_from_depthbuffer(depth5,near,far);depth6=depth_from_depthbuffer(depth6,near,far);
                depth7=depth_from_depthbuffer(depth7,near,far);depth8=depth_from_depthbuffer(depth8,near,far);
                float length = (depth2-depth1)+(depth4-depth3)+(depth6-depth5)+(depth8-depth7);
                return clamp(pow(10.0,-alpha*length),0.0,1.0);
            }
            float absorb8_proj(vec4 depth_coord,float alpha,float near,float far) {
                float coord = depth_from_depthbuffer(depth_coord.p/depth_coord.q,near,far);
                float depth1=texture2DProj(tex2D_1,depth_coord).r;float depth2=texture2DProj(tex2D_2,depth_coord).r;
                float depth3=texture2DProj(tex2D_3,depth_coord).r;float depth4=texture2DProj(tex2D_4,depth_coord).r;
                float depth5=texture2DProj(tex2D_5,depth_coord).r;float depth6=texture2DProj(tex2D_6,depth_coord).r;
                float depth7=texture2DProj(tex2D_7,depth_coord).r;float depth8=texture2DProj(tex2D_8,depth_coord).r;
                depth1=depth_from_depthbuffer(depth1,near,far);depth2=depth_from_depthbuffer(depth2,near,far);
                depth3=depth_from_depthbuffer(depth3,near,far);depth4=depth_from_depthbuffer(depth4,near,far);
                depth5=depth_from_depthbuffer(depth5,near,far);depth6=depth_from_depthbuffer(depth6,near,far);
                depth7=depth_from_depthbuffer(depth7,near,far);depth8=depth_from_depthbuffer(depth8,near,far);
                float diff1=abs(coord-depth1);float diff2=abs(coord-depth2);float diff3=abs(coord-depth3);float diff4=abs(coord-depth4);float diff5=abs(coord-depth5);float diff6=abs(coord-depth6);float diff7=abs(coord-depth7);float diff8=abs(coord-depth8);
                float length = 0.0;
                if ((diff2<diff8)&&(diff2<diff7)&&(diff2<diff6)&&(diff2<diff5)&&(diff2<diff4)&&(diff2<diff3)&&(diff2<diff1)) { length = coord-depth1; }
                if ((diff3<diff8)&&(diff3<diff7)&&(diff3<diff6)&&(diff3<diff5)&&(diff3<diff4)&&(diff3<diff2)&&(diff3<diff1)) { length = depth2-depth1; }
                if ((diff4<diff8)&&(diff4<diff7)&&(diff4<diff6)&&(diff4<diff5)&&(diff4<diff3)&&(diff4<diff2)&&(diff4<diff1)) { length = (depth4-depth3)+(depth2-depth1); }
                if ((diff5<diff8)&&(diff5<diff7)&&(diff5<diff6)&&(diff5<diff4)&&(diff5<diff3)&&(diff5<diff2)&&(diff5<diff1)) { length = (depth4-depth3)+(depth2-depth1); }
                if ((diff6<diff8)&&(diff6<diff7)&&(diff6<diff5)&&(diff6<diff4)&&(diff6<diff3)&&(diff6<diff2)&&(diff6<diff1)) { length = (depth6-depth5)+(depth4-depth3)+(depth2-depth1); }
                if ((diff7<diff8)&&(diff6<diff7)&&(diff5<diff5)&&(diff4<diff4)&&(diff3<diff3)&&(diff2<diff2)&&(diff1<diff1)) { length = (depth6-depth5)+(depth4-depth3)+(depth2-depth1); }
                if ((diff8<diff7)&&(diff8<diff6)&&(diff8<diff5)&&(diff8<diff4)&&(diff8<diff3)&&(diff8<diff2)&&(diff8<diff1)) { length = (depth8-depth7)+(depth6-depth5)+(depth4-depth3)+(depth2-depth1); }
                return clamp(pow(10.0,-alpha*length),0.0,1.0);
            }"""
    return string
def glLibInternal_get_shadow_funcs(renderequation):
    string = ""
##    if   "df_shadowed" in renderequation:
##        #http://www.gamedev.net/community/forums/topic.asp?topic_id=571102
##        string += """
##        const float bias = 0.0001;
##        float gllibinternal_df(sampler2D shadtex,vec2 texel_size,vec2 uv,float depth) {
##            vec2 distance = vec2(0.0,0.0);
##            float ks = 1.0;
##            float count = 0.0;
##            for (float i=-ks;i<=ks;i++) {
##                for (float j=-ks;j<=ks;j++) {
##                    vec2 sample = vec2(i,j)*texel_size;
##
##                    //Shadow test
##                    float test = min(bias,depth-texture2D(shadtex,uv+sample).x)/bias;
##
##                    //This texel's contribution to distance calculation:
##                    distance += sample*test; 
##                    count += test;
##                }
##            }
##            if (count<0.1) { return 1.0; } //No shadowed texels, maximum distance:
##            return length(distance/count) / (ks*sum(texel_size)/2.0); //Return length of the average sample vector
##        }
##        float df_shadowed(sampler2D shadtex,vec2 texture_size,vec4 depth_coord) {
##            vec2 proj = depth_coord.xy/depth_coord.w; 
##            float depth = depth_coord.z/depth_coord.w;
##            
##            vec2 texel_size = 1.0/texture_size;
##
##            float tl = gllibinternal_df(shadtex,texel_size,proj,                                depth);
##            float tr = gllibinternal_df(shadtex,texel_size,proj+vec2(texel_size.x,         0.0),depth);
##            float bl = gllibinternal_df(shadtex,texel_size,proj+vec2(         0.0,texel_size.y),depth);
##            float br = gllibinternal_df(shadtex,texel_size,proj+vec2(texel_size.x,texel_size.y),depth);
##
##            vec2 f = fract(proj.xy*texture_size);
##            float shadow = mix(mix(tl,tr,f.x),
##                               mix(bl,br,f.x),f.y);
##            shadow = smoothstep(0.0,1.0,(shadow-0.5)/(1.0-0.5));
##            
##            return shadow;
##        }"""
    if "shadowed" in renderequation:#elif
        string += """
        float gllibinternal_shadproj(sampler2D shadtex,vec4 depth_coord,float default_color,bool flip_coords) {
            float value = default_color;
            if (depth_coord.w>0.0) {
                vec2 testcoord = depth_coord.xy/depth_coord.w;
                if (testcoord.x>=0.0) { if (testcoord.x<=1.0) { if (testcoord.y>=0.0) { if (testcoord.y<=1.0) {
                    if (!flip_coords) { value = (clamp(depth_coord.z/depth_coord.w,0.0,1.0)<=texture2DProj(shadtex,depth_coord).r) ? 1.0:0.0; }
                    else {
                        value = (clamp(depth_coord.z/depth_coord.w,0.0,1.0)<=texture2D(shadtex,vec2(depth_coord.x/depth_coord.w,1.0-(depth_coord.y/depth_coord.w))).r) ? 1.0:0.0;
                    }
                }}}}
            }
            return value;
        }
        float shadowed(sampler2D shadtex,vec4 depth_coord)                                      { return gllibinternal_shadproj(shadtex,depth_coord,1.0,false); }
        float shadowed(sampler2D shadtex,vec4 depth_coord,bool flip_coords)                     { return gllibinternal_shadproj(shadtex,depth_coord,1.0,flip_coords); }
        float shadowed(sampler2D shadtex,vec4 depth_coord,float default_color)                  { return gllibinternal_shadproj(shadtex,depth_coord,default_color,false); }
        float shadowed(sampler2D shadtex,vec4 depth_coord,float default_color,bool flip_coords) { return gllibinternal_shadproj(shadtex,depth_coord,default_color,flip_coords); }"""
##        if "shadowed_pcf" in renderequation:
##            string += """
##            float shadowed_pcf(sampler2D shadtex,float radius,int kernel=3,float default_color=1.0,bool flip_coords) {
##                float shadow=0.0,value;
##                vec2 testcoord;
##                vec4 coord = vec4(0.0);
##                float depth = ProjCoord.p/ProjCoord.q;
##                for (int v=-kernel; v<=kernel; v++) { for (int u=-kernel; u<=kernel; u++) {
##                    value = default_color;
##                    coord = ProjCoord+(radius*vec4(u,v,0.0,0.0));
##                    testcoord = coord.xy/coord.w;
##                    if (testcoord.x>=0.0) { if (testcoord.x<=1.0) { if (testcoord.y>=0.0) { if (testcoord.y<=1.0) {
##                        value = (depth<=texture2DProj(shadtex,coord).x) ? 1.0:0.0;
##                    }}}}
##                    shadow += value;
##                }}
##                int dim = (2*kernel)+1;
##                return shadow/float(dim*dim);
##            }
##            //float shadowed_pcf(sampler2D shadtex,float radius) {return shadowed_pcf(shadtex,radius,3,1.0);}
##            //float shadowed_pcf(sampler2D shadtex,float radius,int kernel) {return shadowed_pcf(shadtex,radius,kernel,1.0);}
##            //float shadowed_pcf(sampler2D shadtex,float radius,float default_color) {return shadowed_pcf(shadtex,radius,3,default_color);}"""
##        if "shadowed_edges" in renderequation:
##            string += """
##            float ShadProjEdges(sampler2D shadtex,vec4 coord,float default_color) {
##                float value = default_color;
##                value = (coord.p/coord.q<=texture2DProj(shadtex,coord).r) ? 1.0:0.0;
##                return value;
##            }
##        float shadowed_edges(sampler2D shadtex) { return ShadProjEdges(shadtex,ProjCoord,1.0); }
##        float shadowed_edges(sampler2D shadtex,float default_color) { return ShadProjEdges(shadtex,ProjCoord,default_color); }"""
##        if "shadowed_pcf_edges" in renderequation:
##        #NO OPTIONAL ARGS--THIS WON'T WORK
##            string += """
##            float shadowed_pcf_edges(sampler2D shadtex,float radius,int kernel=3) {
##                float shadow=0.0,value;
##                vec2 testcoord;
##                vec4 coord = vec4(0.0);
##                float depth = ProjCoord.p/ProjCoord.q;
##                for (int v=-kernel; v<=kernel; v++) {
##                    for (int u=-kernel; u<=kernel; u++) {
##                        value = default_color;
##                        coord = ProjCoord+(radius*vec4(u,v,0.0,0.0));
##                        value = (depth<=texture2DProj(shadtex,coord).x) ? 1.0:0.0;
##                        shadow += value;
##                    }
##                }
##                int dim = (2*kernel)+1;
##                return shadow/float(dim*dim);
##            }"""
        #http://www.sin.cvut.cz/~micro/viz/doc/shadows_en.pdf
    return string
def glLibInternal_get_cubemap_funcs(renderequation):
    string = ""
    if "cubemap_" in renderequation:
##        distance = (distance-near) / (far-near);
##        shaddepth = 1.0/( shaddepth*-2.0 + 1.0 - ((far+near)/(near-far)) );
        
        string += """
        float cubemap_depthtest(samplerCube cubetex, vec3 center, float near, float far) {
            vec3 lightdir = vec4(transform_matrix*vertex).xyz - center;
            
            float distance = max(max(abs(lightdir.x),abs(lightdir.y)),abs(lightdir.z));
            distance = ((far+near)/(far-near)) + (1.0/distance)*((-2.0*far*near)/(far-near));
            distance = (distance+1.0)/2.0;
            
            float shaddepth = textureCube(cubetex,normalize(lightdir)).r;

            if (distance>shaddepth) { return 0.0; }
            else                    { return 1.0; }
        }"""
        if "cubemap_normal" in renderequation:
            string += """
        vec3 cubemap_normal() {
            return vec4(vec4(normalize(mat3(t,b,n)*vec3(0.0,0.0,1.0)),1.0)*gl_ModelViewMatrix).xyz;
        }
        vec3 cubemap_normal_from_normalmap(vec3 normalmapsample) {
            return vec4(vec4(normal_from_normalmap(normalmapsample),1.0)*gl_ModelViewMatrix).xyz;
        }"""
        if "cubemap_ref" in renderequation:
            string += """
        vec4 cubemap_reflect_sample(samplerCube cubetex, vec3 cubemapnormal) {
            vec3 dir = vec4(vertex-gl_ModelViewMatrixInverse[3]).xyz;
            vec3 reflectvec = vec4(transform_matrix*vec4(reflect(dir,cubemapnormal),1.0)).xyz;
            return textureCube(cubetex,reflectvec);
        }
        vec4 cubemap_refract_sample(samplerCube cubetex, vec3 cubemapnormal, float eta) {
            vec3 dir = vec4(vertex-gl_ModelViewMatrixInverse[3]).xyz;
            vec3 refract_normal = cubemapnormal;
            float refract_eta = eta;
            if (dot(dir,cubemapnormal)>0.0) { eta = 1.0/eta; refract_normal *= -1.0; }
            vec3 refractvec = vec4(transform_matrix*vec4(refract(dir,refract_normal,refract_eta),1.0)).xyz;
            return textureCube(cubetex,refractvec);
        }"""
    return string
def glLibInternal_get_light_funcs(renderequation):
    string = ""
    if "fresnel_coefficient" in renderequation:
        #http://www.cse.ohio-state.edu/~kerwin/refraction.html
        string += """
        vec2 fresnel_coefficient(float n1,float n2) {
            float eta = n2 / n1;
            
            float cos_theta1 = dot(E,normal);
            float cos_theta2 = sqrt(1.0-(eta*eta*( 1.0-cos_theta1*cos_theta1)));
            
            vec3 reflection = E - 2.0*cos_theta1*normal;
            vec3 refraction = eta*E + (cos_theta2 - eta*cos_theta1)*normal;
            
            float fresnel_rs = (n2*cos_theta1 - n1*cos_theta2) / (n2*cos_theta1 + n1*cos_theta2);
            float fresnel_rp = (n1*cos_theta1 - n2*cos_theta2) / (n1*cos_theta1 + n2*cos_theta2);
            
            float reflectance = (fresnel_rs*fresnel_rs + fresnel_rp*fresnel_rp) / 2.0;
            reflectance = reflectance>1.0 ? 0.0:reflectance;
            float transmittance = 1.0-reflectance;
            
            return vec2(reflectance,transmittance);
        }"""
    if "light_" in renderequation:
        string += """
        float abs_diffuse_coefficient(gl_LightSourceParameters light) {
            vec3 l = normalize(light.position.xyz-vVertex);
            return abs(dot(normal,l));
        }
        float abs_specular_coefficient_ph(gl_LightSourceParameters light) {
            vec3 l = normalize(light.position.xyz-vVertex);
            vec3 reflected = reflect(-l,normal);
            return abs(dot(reflected,E));
        }
        
        float diffuse_coefficient(gl_LightSourceParameters light) {
            vec3 l = normalize(light.position.xyz-vVertex);
            return max(dot(normal,l),0.0);
        }
        float specular_coefficient_ph(gl_LightSourceParameters light) {
            return max(dot(reflect(normalize(vVertex-light.position.xyz),normal),E),0.0);
        }
        float specular_coefficient_bl(gl_LightSourceParameters light) {
            return max(dot(normal,-normalize(light.halfVector.xyz)),0.0);
        }
        float specular_coefficient_gs(gl_LightSourceParameters light) {
            return exp(-pow(specular_coefficient_bl(light)/0.9,2.0));
        }
        float specular_coefficient_bk(gl_LightSourceParameters light, float m) {
            float NdotH = dot(normal,normalize(light.halfVector.xyz));
            float exponent = -pow( tan(acos(NdotH))/m, 2.0 );
            return exp(exponent)/(4.0*m*m*pow(NdotH,4.0));
        }
        vec4 light_ambient(gl_LightSourceParameters light) {
            return light.ambient;
        }
        vec4 light_diffuse(gl_LightSourceParameters light) {
            float coeff = diffuse_coefficient(light);
            return light.diffuse*coeff;
        }
        vec4 light_specular_ph(gl_LightSourceParameters light) { float coeff = specular_coefficient_ph(light); float powexp = pow(coeff,clamp(gl_FrontMaterial.shininess,0.001,128.0)); return light.specular*powexp; }
        vec4 light_specular_bl(gl_LightSourceParameters light) { float coeff = specular_coefficient_bl(light); float powexp = pow(coeff,clamp(gl_FrontMaterial.shininess,0.001,128.0)); return light.specular*powexp; }
        vec4 light_specular_gs(gl_LightSourceParameters light) { float coeff = specular_coefficient_gs(light); float powexp = pow(coeff,clamp(gl_FrontMaterial.shininess,0.001,128.0)); return light.specular*powexp; }
        vec4 light_specular_bk(gl_LightSourceParameters light, float m) { float coeff = specular_coefficient_bk(light,m); return light.specular*coeff; }
        float light_att(gl_LightSourceParameters light) {
            vec3 l = light.position.xyz-vVertex.xyz;
            float dist = length(l);
            float cons = light.constantAttenuation;
            float linear = light.linearAttenuation * dist;
            float quad = light.quadraticAttenuation * dist * dist;
            float denom = cons + linear + quad;
            return clamp(1.0/denom,0.0,1.0);
        }"""
        if "abs_light" in renderequation:
            string += """
        vec4 abs_light_diffuse(gl_LightSourceParameters light) {
            float coeff = abs_diffuse_coefficient(light);
            return light.diffuse*coeff;
        }
        vec4 abs_light_specular_ph(gl_LightSourceParameters light) {
            float coeff = abs_specular_coefficient_ph(light);
            float powexp = pow(coeff,clamp(gl_FrontMaterial.shininess,0.001,128.0));
            return light.specular*powexp;
        }"""
        if "light_spot" in renderequation:
            string += """
        float light_spot(gl_LightSourceParameters light) {
	    float dot_LD = dot( normalize(vVertex-light.position.xyz), normalize(light.spotDirection) );
	    float coeff = 1.0 - (1.0-dot_LD)/(1.0-light.spotCosCutoff);
	    return (dot_LD>light.spotCosCutoff) ? pow(coeff,light.spotExponent) : 0.0;

        }"""
    return string
def glLibInternal_get_caustic_func(renderequation):
    string = ""
    if "add_caustics" in renderequation:
        string += """
        vec3 add_caustics(sampler2D caustictex,vec4 projcoord) {
            vec3 value = vec3(0.0);
            vec2 testcoord = projcoord.xy/projcoord.w;
            if (testcoord.x>=0.0) { if (testcoord.x<=1.0) { if (testcoord.y>=0.0) { if (testcoord.y<=1.0) { value = texture2DProj(caustictex,projcoord).rgb; }}}}
            return value;
        }"""
    return string
def glLibInternal_get_rotation_funcs(section):
    string = ""
    if "rotation_matrix_" in section:
        string += """
        mat3 rotation_matrix_x(float angle) {
            float cos_angle=cos(angle);float sin_angle=sin(angle);
            return mat3(vec3(1.0,0.0,       0.0      ),
                        vec3(0.0,cos_angle,-sin_angle),
                        vec3(0.0,sin_angle, cos_angle));
        }
        mat3 rotation_matrix_y(float angle) {
            float cos_angle=cos(angle);float sin_angle=sin(angle);
            return mat3(vec3( cos_angle,0.0,sin_angle),
                        vec3( 0.0,      1.0,0.0      ),
                        vec3(-sin_angle,0.0,cos_angle));
        }
        mat3 rotation_matrix_z(float angle) {
            float cos_angle=cos(angle);float sin_angle=sin(angle);
            return mat3(vec3(cos_angle,-sin_angle,0.0),
                        vec3(sin_angle, cos_angle,0.0),
                        vec3(0.0,       0.0,      1.0));
        }
        mat3 rotation_matrix_arbitrary(vec3 vec,float angle) {
            float c=cos(angle);float s=sin(angle);
            float C = 1.0 - c;
            float  xs = vec.x* s; float  ys = vec.y* s; float  zs = vec.z* s;
            float  xC = vec.x* C; float  yC = vec.y* C; float  zC = vec.z* C;
            float xyC = vec.x*yC; float yzC = vec.y*zC; float zxC = vec.z*xC;
            return mat3(vec3(vec.x*xC+c,    xyC-zs,    zxC+ys),
                        vec3(    xyC+zs,vec.y*yC+c,    yzC-xs),
                        vec3(    zxC-ys,    yzC+xs,vec.z*zC+c));
        }"""
    return string
def glLibInternal_get_texture_funcs(section):
    string = ""
##    if "texture2Dcf" in section:
##        string += """
##        vec4 texture2Dcf(sampler2D texture, vec2 size, vec2 coord) {
##            vec2 pixel_coord = coord*size;
##            vec2 pixel_intersect_loc = round(pixel_coord);
##            vec2 p00 = pixel_intersect_loc - vec2(0.5);
##            vec2 p11 = p00 + vec2(1.0);
##            vec2 part = pixel_intersect_loc - pixel_coord;
##            part = -part+0.5;
##            p00 /= size;
##            p11 /= size;
##            vec4 h00 = texture2D(texture,vec2(p00.x,p00.y));
##            vec4 h10 = texture2D(texture,vec2(p11.x,p00.y));
##            vec4 h01 = texture2D(texture,vec2(p00.x,p11.y));
##            vec4 h11 = texture2D(texture,vec2(p11.x,p11.y));
##            vec2 height = -2.0*pow(part,3.0)+3.0*pow(part,2.0);
##            vec4 x0 = h00 + height.x*(h10-h00);
##            vec4 x1 = h01 + height.x*(h11-h01);
##            vec4 result = x0 + height.y*(x1-x0);
##            return result;
##        }"""
    if "texture2Dbc" in section:
        string += """
        vec4 texture2Dbc(sampler2D texture, vec2 size, vec2 coord, float a) {
            return ;
        }"""
    return string










        
