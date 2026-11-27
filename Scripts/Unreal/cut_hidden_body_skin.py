"""Deletes the MetaHuman body skin hidden under our outfit (hoodie, cargo pants, sneakers): keeps only triangles skinned to the
hands, so skin never pokes through clothes on bigger bodies. Run in the editor after every MetaHuman rebuild (the build
regenerates the body mesh): exec(open(path).read()); cut("/Game/.../Body/SKM_MHC_<Name>_BodyMesh"). All source LODs."""
import unreal
GA=unreal.GeometryScript_AssetUtils; Q=unreal.GeometryScript_MeshQueries; BW=unreal.GeometryScript_BoneWeights; ME=unreal.GeometryScript_MeshEdits; GL=unreal.GeometryScript_List
VIS=("hand_","thumb_","index_","middle_","ring_","pinky_","wrist_outer")
def cut(path):
    skm=unreal.load_asset(path); sms=unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem); nlod=sms.get_lod_count(skm) if sms and hasattr(sms,"get_lod_count") else 8; out=[("lods",nlod)]
    for lod in range(nlod):
        dm=unreal.DynamicMesh()
        _,res=GA.copy_mesh_from_skeletal_mesh(skm, dm, unreal.GeometryScriptCopyMeshFromAssetOptions(), unreal.GeometryScriptMeshReadLOD(lod_type=unreal.GeometryScriptLODType.SOURCE_MODEL, lod_index=lod))
        if res!=unreal.GeometryScriptOutcomePins.SUCCESS: out.append((lod,"read fail")); break
        names=[str(b.get_editor_property("name")) for b in BW.get_all_bones_info(dm)[1]]
        vis=[]
        for v in range(Q.get_vertex_count(dm)):
            _,w,ok=BW.get_largest_vertex_bone_weight(dm, v); vis.append(ok and names[w.bone_index].startswith(VIS))
        kill=[]
        for t in range(Q.get_num_triangle_i_ds(dm)):
            ia,ok=Q.get_triangle_indices(dm,t)
            if ok and (vis[ia.x]+vis[ia.y]+vis[ia.z])<2: kill.append(t)
        n0=Q.get_num_triangle_i_ds(dm)
        il=GL.convert_array_to_index_list(kill, unreal.GeometryScriptIndexType.TRIANGLE) if hasattr(GL,'convert_array_to_index_list') else None
        ME.delete_triangles_from_mesh(dm, il)
        _,res2=GA.copy_mesh_to_skeletal_mesh(dm, skm, unreal.GeometryScriptCopyMeshToAssetOptions(), unreal.GeometryScriptMeshWriteLOD(lod_index=lod))
        out.append((lod, n0, len(kill), str(res2)))
    ok=unreal.EditorAssetLibrary.save_loaded_asset(skm, False)
    return out, ok
