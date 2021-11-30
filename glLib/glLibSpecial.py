from glLibLocals import *
from glLibMath import *

def glLibFilterSurface(surface,kernel):
    if not GLLIB_SURFARRAY_AVAILABLE: raise glLibError("Error: Cannot blur surface; surfarray not available!")
    arr = pygame.surfarray.array3d(surface)
    final_array = np.zeros((surface.get_width(),surface.get_height(),3))
    max_value = 0.0
    row_trans = -(len(kernel)/2)
    for row in kernel:
        column_trans = -(len(row)/2)
        for operation in row:
            final_array += operation*np.roll(np.roll(arr,row_trans,1),column_trans,0)
            max_value += operation
            column_trans += 1
        row_trans += 1
    return pygame.surfarray.make_surface(final_array/max_value)
def glLibHeightmapToNormalmap(heightsurf,purturb_level,bundle_height=False):
    size = heightsurf.get_size()
    normal_surf = pygame.Surface([size[0]-1,size[1]-1])
    if bundle_height:
        try:
            normal_surf = normal_surf.convert_alpha()
        except:
            pygame.display.set_mode((1,1))
            normal_surf = normal_surf.convert_alpha()
            pygame.display.quit()
    xdifferences = []
    ydifferences = []
    heights = []
    for x in xrange(size[0]-1):
        xdiffrow = []
        ydiffrow = []
        heightrow = []
        for y in xrange(size[1]-1):
            color_tl = heightsurf.get_at((x,  y  ))[0]
            color_tr = heightsurf.get_at((x+1,y  ))[0]
            color_bl = heightsurf.get_at((x,  y+1))[0]
            color_br = heightsurf.get_at((x+1,y+1))[0]
            xdiff = ((color_tl+color_bl)-(color_tr+color_br))/2.0#(((color_tl+color_bl)/2.0)-((color_tr+color_br)/2.0))
            ydiff = ((color_br+color_bl)-(color_tr+color_tl))/2.0#(((color_br+color_bl)/2.0)-((color_tr+color_tl)/2.0))
            xdiffrow.append(xdiff)
            ydiffrow.append(ydiff)
            heightrow.append((color_tl+color_bl+color_tr+color_br)/4.0)
        xdifferences.append(xdiffrow)
        ydifferences.append(ydiffrow)
        heights.append(heightrow)
    for diffrowindex in xrange(len(xdifferences)):
        for differenceindex in xrange(len(xdifferences[0])):
            xdiff = (xdifferences[diffrowindex][differenceindex]/255.0)*purturb_level
            ydiff = (ydifferences[diffrowindex][differenceindex]/255.0)*purturb_level
            vector = normalize([  xdiff,  ydiff,  1.0  ])
            vector = sc_vec(255.0,vector)
            vector = [int(round(127.5+0.5*vector[0])),int(round(127.5+0.5*vector[1])),int(round(vector[2]))]
            if bundle_height:
                vector.append(heights[diffrowindex][differenceindex])
            normal_surf.set_at((diffrowindex,differenceindex),vector)
    return normal_surf
