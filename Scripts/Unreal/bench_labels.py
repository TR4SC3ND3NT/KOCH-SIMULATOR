# UE 5.8 editor script (R4, playtest aid): numbers every placed bench (PROP_* bench actors) with a big red number
# 1.6 m above it, drawn on four faces so it reads from any side, and writes Saved/QA/bench_numbers.json (number ->
# placeholder name). The owner names numbers to flip; those go into Scripts/Unreal/bench_flips.json, which
# place_props.py applies after its orientation rule. Run with --remove to delete the labels.
# Run (Output Log, Cmd = Python): py "<repo>/Scripts/Unreal/bench_labels.py" [--remove]
import json
import os
import sys

import unreal

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TAG = "KochBenchLabel"


def main():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = eas.get_all_level_actors()
    eas.destroy_actors([a for a in actors if a.actor_has_tag(TAG)])
    if "--remove" in sys.argv:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
        unreal.log("bench_labels: removed")
        return
    benches = []
    for a in actors:
        tags = [str(t) for t in a.tags]
        if "KochProp" not in tags or "Bench" not in a.get_editor_property("static_mesh_component").get_editor_property("static_mesh").get_name():
            continue
        if "_INT_" in a.get_actor_label():
            continue                                         # indoor hall benches: not part of this review
        ph = next((t.split(":", 1)[1] for t in tags if t.startswith("Replaces:")), a.get_actor_label())
        benches.append((ph, a))
    benches.sort(key=lambda b: b[0])
    numbers = {}
    for n, (ph, a) in enumerate(benches, 1):
        loc = a.get_actor_location()
        yaw = a.get_actor_rotation().yaw
        for k, dyaw in enumerate((0.0, 90.0, 180.0, 270.0)):   # four faces: readable from every side
            t = eas.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(loc.x, loc.y, loc.z + 160),
                                           unreal.Rotator(roll=0, pitch=0, yaw=yaw + dyaw))
            c = t.get_editor_property("text_render")
            c.set_text(str(n))
            c.set_world_size(60.0)
            c.set_text_render_color(unreal.Color(r=255, g=30, b=30, a=255))
            c.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
            t.set_actor_label(f"BENCHNUM_{n:03d}_{k}")
            t.set_folder_path("Review/BenchNumbers")
            t.set_editor_property("tags", [unreal.Name(TAG)])
        numbers[n] = ph
    out = os.path.join(REPO, "Saved", "QA")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "bench_numbers.json"), "w", encoding="utf-8") as fh:
        json.dump(numbers, fh, indent=1)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"bench_labels: {len(numbers)} benches numbered")


main()
