import bpy, json
from mathutils import Vector
out={}
for o in bpy.data.objects:
    if o.type!='MESH': continue
    bb=[o.matrix_world@Vector(c) for c in o.bound_box]
    xs=[b.x for b in bb]; ys=[b.y for b in bb]; zs=[b.z for b in bb]
    mats=sorted({s.material.name for s in o.material_slots if s.material})
    out[o.name]=[round(min(xs),3),round(max(xs),3),round(min(ys),3),round(max(ys),3),round(min(zs),3),round(max(zs),3),mats[:4]]
json.dump(out,open('/tmp/claude-0/-home-user-KOCH-SIMULATOR/4c46a856-9b83-58ac-a5d2-3a1adfa042aa/scratchpad/agent_scratch/pass1_part0/bbox.json','w'))
print(len(out))
