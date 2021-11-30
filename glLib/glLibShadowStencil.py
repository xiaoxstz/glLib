from glLibLocals import *
from glLibMath import *
import time
#Depth Fail = rear must be capped; camera in volume is ok
pi_over_two = pi/2.0
##def glLibInternal_write_dict_tree(vec,value,dictionary):
##    dictionary_tree = [dictionary]
##    for key in vec[:-1]:
##        if key in dictionary_tree[-1]:
##            dictionary_tree.append(dictionary_tree[-1][key])
##        else:
##            dictionary_tree.append({})
##    dictionary_tree[-1][vec[-1]] = value
##    vec.reverse()
##    index = 0
##    for dictionary in dictionary_tree[1:]:
##        dictionary_tree[-2][vec[index+1]] = dictionary_tree[-1]
##        dictionary_tree.remove(dictionary_tree[-1])
##        index += 1
##    vec.reverse()
##    return dictionary_tree[0]
####def glLibInternal_expand_dictionary(dictionary):
####    values = {1:dictionary}
####    for key in dictionary_tree[-1].keys():
####        values[key] = dictionary_tree[-1][key]
####    values.append(value)
##def glLibInternal_in_dict_tree(vec,dictionary):
##    try: glLibInternal_read_dict_tree(vec); return True
##    except: return False
##def glLibInternal_read_dict_tree(vec,dictionary):
##    subdict = dict(dictionary)
##    for key in vec:
##        subdict = subdict[key]
##    return subdict
def glLibInternal_less_than(face,lightpos):
    return abs_angle_between_rad(face[1],vec_subt(face[0][0],lightpos))<pi_over_two and \
           abs_angle_between_rad(face[1],vec_subt(face[0][1],lightpos))<pi_over_two and \
           abs_angle_between_rad(face[1],vec_subt(face[0][2],lightpos))<pi_over_two
#indices
#store normals with edges, and sort x.  Test every edge
#
def glLibInternal_edges(object,lightpos):
    edges = {}
    t1 = time.time()
    for sublist in range(object.number_of_lists):
        face_data = object.light_volume_face_data[sublist]
        for indices in face_data: #v1,v2,v3,n
            normal = object.transformed_normals[sublist][indices[3]]
            v1 = object.transformed_vertices[sublist][indices[0]]
            if abs_angle_between_rad(normal,vec_subt(v1,lightpos))<pi_over_two:
                for p1,p2 in [[indices[0],indices[1]],
                              [indices[1],indices[2]],
                              [indices[2],indices[0]]]:
                    edge = [p1,p2]
                    edge.sort()
                    edge = tuple(edge)
                    if edge in edges: edges[edge][1] += 1
                    else:             edges[edge] = [[p1,p2],1]
    t2 = time.time()
##    print t2-t1 #0.01
    edges2 = []
    for edge_data in edges.values():
        if edge_data[1] == 1:
            p1 = object.transformed_vertices[sublist][edge_data[0][0]]
            p2 = object.transformed_vertices[sublist][edge_data[0][1]]
            edges2.append([p1,p2])
    return edges2
def glLibExtrudeLightVolumes(light,object,front,back):
    lightpos = light.get_pos()
    t1 = time.time()
    edges = glLibInternal_edges(object,lightpos)
    t2 = time.time()
    #Draw geometry
    #   Draw volume
    dllist = glGenLists(1)
    glNewList(dllist,GL_COMPILE)
    glBegin(GL_QUADS)
    for p1,p2 in edges:
        np1 = normalize(vec_subt(lightpos,p1))
        np2 = normalize(vec_subt(lightpos,p2))
        glVertex3f(  *vec_add(p1,sc_vec(-front,np1))  )
        glVertex3f(  *vec_add(p2,sc_vec(-front,np2))  )
        glVertex3f(  *vec_add(p2,sc_vec(-back, np2))  )
        glVertex3f(  *vec_add(p1,sc_vec(-back, np1))  )
    glEnd()
    #   Draw caps
    glBegin(GL_TRIANGLES)
    for sublist in range(object.number_of_lists):
        face_data = object.light_volume_face_data[sublist]
        for indices in face_data: #v1,v2,v3,n
            normal = object.transformed_normals[sublist][indices[3]]
            v1,v2,v3 = [ object.transformed_vertices[sublist][indices[i]] for i in range(3) ]
            if abs_angle_between_rad(normal,vec_subt(v1,lightpos))<pi_over_two:
                glVertex3f(*vec_add(v1,sc_vec(-back,normalize(vec_subt(lightpos,v1)))))
                glVertex3f(*vec_add(v2,sc_vec(-back,normalize(vec_subt(lightpos,v2)))))
                glVertex3f(*vec_add(v3,sc_vec(-back,normalize(vec_subt(lightpos,v3)))))
            else:
                glVertex3f(*vec_add(v1,sc_vec(-front,normalize(vec_subt(lightpos,v1)))))
                glVertex3f(*vec_add(v2,sc_vec(-front,normalize(vec_subt(lightpos,v2)))))
                glVertex3f(*vec_add(v3,sc_vec(-front,normalize(vec_subt(lightpos,v3)))))
    glEnd()
    glEndList()
    t3 = time.time()
##    print "Find edge list:",round(t2-t1,4)
##    print "Make list:",round(t3-t2,4)
    return dllist
##def glLibTransformLightVolumeData(object,translate_point,rotate_point):
##    object.transformed_vertices = {}
##    object.transformed_normals = {}
##    for sublist in range(object.number_of_lists):
##        object.transformed_vertices[sublist] = []
##        object.transformed_normals [sublist] = []
##        t1 = time.time()
##        for index in range(len(object.raw_vertices)):
####            object.transformed_vertices[sublist].append(translate_point(object.raw_vertices[index]))
##            object.transformed_vertices[sublist].append(translate_point(rotate_point(object.raw_vertices[index])))
##        t2 = time.time()
##        for index in range(len(object.raw_normals )):
##            object.transformed_normals [sublist].append(rotate_point(object.raw_normals[index]))
##        t3 = time.time()
####        print "transform vertices:",t2-t1,"data amount:",len(object.raw_vertices)
####        print "transform normals:",t3-t2,"data amount:",len(object.raw_normals)
def glLibTransformLightVolumeData(object,translate_points,rotate_points):
    object.transformed_vertices = {}
    object.transformed_normals = {}
    for sublist in range(object.number_of_lists):
        t1 = time.time()
        object.transformed_vertices[sublist] = translate_points(rotate_points(object.raw_vertices)).tolist()
        t2 = time.time()
        object.transformed_normals [sublist] = rotate_points(object.raw_normals).tolist()
        t3 = time.time()
##        print "transform vertices:",t2-t1,"data amount:",len(object.raw_vertices)
##        print "transform normals:",t3-t2,"data amount:",len(object.raw_normals)
def glLibDrawWithShadowVolumes(drawsceneshadowedfunc,drawscenelitfunc,drawvolfunc):
    drawsceneshadowedfunc()

    glEnable(GL_STENCIL_TEST)
    glClear(GL_STENCIL_BUFFER_BIT)
    glStencilFunc(GL_ALWAYS,0,0xFFFFFFFF)
    
    
    glDisable(GL_LIGHTING)
    glDisable(GL_TEXTURE_2D)
    glDepthMask(False)
    glColorMask(False,False,False,False)
    glEnable(GL_CULL_FACE)

    glCullFace(GL_FRONT)
    glStencilOp(GL_KEEP,GL_INCR,GL_KEEP)
    drawvolfunc()
    glCullFace(GL_BACK)
    glStencilOp(GL_KEEP,GL_DECR,GL_KEEP)
    drawvolfunc()

    glDisable(GL_CULL_FACE)
    glDepthMask(True)
    glColorMask(True,True,True,True)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_LIGHTING)
    

    glStencilFunc(GL_EQUAL,0,0xFFFFFFFF)
    glStencilOp(GL_KEEP,GL_KEEP,GL_KEEP)
    drawscenelitfunc()
    glDisable(GL_STENCIL_TEST)
