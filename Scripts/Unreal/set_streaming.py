# UE 5.8 editor script (R4 -> everyone): World Partition streaming split. The skyline (context blocks, far ground) is
# cheap (Nanite boxes + one 16 km grid, no textures on the facades) but must never pop or vanish, so it stays always
# loaded; everything else (campus detail, props, foliage) keeps streaming by distance on the runtime grid. Idempotent.
# Run (Output Log, Cmd = Python): py "<repo>/Scripts/Unreal/set_streaming.py"
import unreal

LEVEL = "/Game/KochSimulator/Maps/L_GreyboxTest"
ALWAYS = ("CTX_", "GB_CTX_", "GB_BLD_", "FarGround")


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if ues.get_editor_world().get_path_name().split(".")[0] != LEVEL:
        les.load_level(LEVEL)
    wpl = unreal.WorldPartitionBlueprintLibrary
    res = wpl.get_actor_descs()
    wpl.load_actors([d.get_editor_property("guid") for d in (res[1] if isinstance(res, tuple) else res)])
    n = 0
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if a.get_actor_label().startswith(ALWAYS) and a.get_editor_property("is_spatially_loaded"):
            a.modify()
            a.set_editor_property("is_spatially_loaded", False)
            n += 1
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"set_streaming: {n} actors made always loaded")


main()
