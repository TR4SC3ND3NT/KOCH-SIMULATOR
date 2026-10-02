import bpy, json
from mathutils import Vector
out={}
for o in bpy.data.objects:
    if o.type not in ('MESH','CURVE'): continue
    bb=[o.matrix_world @ Vector(c) for c in o.bound_box]
    xs=[v.x for v in bb]; ys=[v.y for v in bb]; zs=[v.z for v in bb]
    out[o.name]=[min(xs),min(ys),min(zs),max(xs),max(ys),max(zs)]
json.dump(out,open('/tmp/claude-0/-home-user-KOCH-SIMULATOR/4c46a856-9b83-58ac-a5d2-3a1adfa042aa/scratchpad/agent_scratch/pass1_part1/bb.json','w'))
print(len(out))
