# FBX writer for ue_prep (inside Blender; used by run.py): one file per static mesh = render mesh node SM_<Name> at
# the origin + its UBX_/UCX_SM_<Name>_NN collision nodes, flat (no parenting: UE-239476), from a private scene.
# FBX settings = Epic Send2UE defaults (github.com/EpicGamesExt/BlenderTools send2ue/resources/settings.json):
# forward Y, up Z, apply unit scale, FBX_SCALE_NONE, no space-transform bake -> UE cm, see common.py for the axes.
import os

import bpy
import numpy as np

FBX_KW = dict(use_selection=True, object_types={"MESH"}, use_custom_props=False, global_scale=1.0,
              apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE", axis_forward="Y", axis_up="Z",
              bake_space_transform=False, mesh_smooth_type="FACE", use_mesh_modifiers=False, use_mesh_edges=False,
              use_tspace=False, use_triangles=False, use_metadata=True, bake_anim=False, add_leaf_bones=False,
              embed_textures=False, path_mode="STRIP", colors_type="NONE", use_subsurf=False)


class Writer:
    def __init__(self):
        self.scene = bpy.data.scenes.new("_ue_prep_export")
        self.scene.unit_settings.system = "METRIC"
        self.scene.unit_settings.scale_length = 1.0
        self.vl = self.scene.view_layers[0]
        self.mats = {}

    def _mat(self, name):
        m = self.mats.get(name)
        if m is None:
            m = bpy.data.materials.get(name)
            if m is None or m.library is not None:
                m = bpy.data.materials.new(name)
            self.mats[name] = m
        return m

    def _mesh(self, name, co, loop_start, loop_vert, slots=None, face_slot=None, smooth=None, uv=None):
        me = bpy.data.meshes.new(name)
        me.vertices.add(len(co))
        me.vertices.foreach_set("co", np.ascontiguousarray(co, np.float32).ravel())
        me.loops.add(len(loop_vert))
        me.loops.foreach_set("vertex_index", np.ascontiguousarray(loop_vert, np.int32))
        me.polygons.add(len(loop_start))
        me.polygons.foreach_set("loop_start", np.ascontiguousarray(loop_start, np.int32))
        me.update(calc_edges=True)
        if slots:
            for s in slots:
                me.materials.append(self._mat(s))
            me.polygons.foreach_set("material_index", np.ascontiguousarray(face_slot, np.int32))
        if smooth is not None:
            me.polygons.foreach_set("use_smooth", np.ascontiguousarray(smooth, bool))
        if uv is not None:
            lay = me.uv_layers.new(name="UVMap")
            lay.uv.foreach_set("vector", np.ascontiguousarray(uv, np.float32).ravel())
        return me

    def _obj(self, name, me):
        ob = bpy.data.objects.new(name, me)
        if ob.name != name:   # a clash would silently rename the node and break the UCX pairing
            raise RuntimeError(f"ue_prep: object name clash {name!r} -> {ob.name!r}")
        self.scene.collection.objects.link(ob)
        return ob

    def write(self, path, name, geo, uv, prims):
        """geo: Geo in asset space (m); uv (L,2); prims: [(prefix, verts, tris)]. Returns used slot names."""
        used = np.unique(geo.face_slot)
        remap = np.zeros(max(int(used.max()) + 1, 1), np.int64)
        remap[used] = np.arange(len(used))
        slots = [geo.slots[i] for i in used]
        obs = [self._obj(name, self._mesh(name, geo.co, geo.loop_start, geo.loop_vert, slots,
                                          remap[geo.face_slot], geo.smooth, uv))]
        nn = {}
        for prefix, v, t in prims:
            k = nn.get(prefix, 0)
            nn[prefix] = k + 1
            pname = f"{prefix}_{name}_{k:02d}"
            t = np.asarray(t, np.int64)
            obs.append(self._obj(pname, self._mesh(pname, v, np.arange(len(t)) * 3, t.ravel())))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with bpy.context.temp_override(scene=self.scene, view_layer=self.vl, selected_objects=obs,
                                           active_object=obs[0]):
                bpy.ops.export_scene.fbx(filepath=path, **FBX_KW)
        finally:
            for ob in obs:
                me = ob.data
                bpy.data.objects.remove(ob, do_unlink=True)
                bpy.data.meshes.remove(me)
        return slots

    def close(self):
        bpy.data.scenes.remove(self.scene)
