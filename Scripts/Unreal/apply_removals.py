# UE 5.8 editor script (R4 -> everyone): greybox elements the owner says are not on the real site
# (Scripts/Unreal/owner_removed.json, from in-game review marks). Their placeholder is hidden with no collision and
# whatever replaced it (vegetation/props tagged Replaces:<name>) is deleted. place_vegetation.py skips the same names.
# Reported to R1 in docs/reference/r1_greybox_issues.md. Idempotent.
# Run (Output Log, Cmd = Python): py "<repo>/Scripts/Unreal/apply_removals.py"
import json
import os

import unreal

LEVEL = "/Game/KochSimulator/Maps/L_GreyboxTest"
LIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "owner_removed.json")


def removed_names():
    with open(LIST, encoding="utf-8") as fh:
        return set(json.load(fh))


def hide(ph):
    ph.modify()   # external (OFPA) actor: without Modify the change is lost on save
    comp = ph.get_editor_property("static_mesh_component")
    comp.modify()
    comp.set_visibility(False, True)
    comp.set_collision_profile_name("NoCollision")
    ph.set_actor_hidden_in_game(True)


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if ues.get_editor_world().get_path_name().split(".")[0] != LEVEL:
        les.load_level(LEVEL)
    wpl = unreal.WorldPartitionBlueprintLibrary
    res = wpl.get_actor_descs()
    wpl.load_actors([d.get_editor_property("guid") for d in (res[1] if isinstance(res, tuple) else res)])
    names = removed_names()
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = eas.get_all_level_actors()
    gone = [a for a in actors if any(str(t) == f"Replaces:{n}" for t in a.tags for n in names)]
    eas.destroy_actors(gone)
    hidden = 0
    for a in actors:
        if a.get_actor_label() in names and a.actor_has_tag("KochGreybox"):
            hide(a)
            hidden += 1
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"apply_removals: {hidden} placeholders hidden, {len(gone)} replacements deleted")


if __name__ == "__main__":
    main()
