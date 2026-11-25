# UE 5.8 editor script (R3, slice video): renders the Checkpoint 1 walk "street -> checkpoint" to MP4.
# A first-person camera at eye height (ground + 165 cm) walks at 1.4 m/s from the bus-stop side of the street over the
# zebra crossing to the turnstile, looks left and right at the curb, and stops facing the guard. Head bob is a small
# step-synchronous sine (1.2 cm, 2 steps/s), well under motion-sickness levels. The ground is traced, so the path follows
# the real kerbs and paving.
# Creates /Game/KochSimulator/Cinematics/LS_CP1_StreetToCheckpoint (rebuilt on every run) and renders it with Movie
# Render Queue in PIE with the MP4 encoder (no pawn: MoviePipelineGameOverrideSetting), 1920x1080, 30 fps.
# Needs the MovieRenderPipeline plugin: start the editor with -EnablePlugins=MovieRenderPipeline (not in the .uproject).
# Output: <repo>/Saved/MovieRenders/KOCH_CP1_street_to_checkpoint.mp4
# Run (Output Log, Cmd = Python): py "<repo>/Scripts/Unreal/render_cp1_walk.py"
import math
import os

import unreal

SEQ_DIR = "/Game/KochSimulator/Cinematics"
SEQ_NAME = "LS_CP1_StreetToCheckpoint"
FPS = 30
EYE = 165.0         # cm above the ground
SPEED = 140.0       # cm/s walking
STEP_HZ = 2.0       # steps per second
BOB = 1.2           # cm
OUT_DIR = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "MovieRenders")
OUT_NAME = "KOCH_CP1_street_to_checkpoint"

# (x, y, yaw at this point, seconds to pause here). UE axes: +X east, +Y south; yaw -90 looks north (towards the gate).
ROUTE = [
    (15500, 13050, -90, 1.5),   # bus-stop side, the gate across the road
    (15485, 12520, -90, 0.0),
    (15480, 12470, -55, 0.8),   # at the curb: look right...
    (15480, 12469, -125, 0.8),  # ...and left
    (15478, 12468, -90, 0.0),
    (15430, 11090, -90, 0.0),   # across the zebra
    (15560, 10900, -91, 0.0),
    (15600, 10680, -90, 3.0),   # under the canopy's edge: the guard at the turnstile, 4.5 m ahead
]


def ground(world, x, y, top=880.0):
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, top), unreal.Vector(x, y, -1000.0),
                                                 unreal.TraceTypeQuery.ECC_VISIBILITY, True, [],
                                                 unreal.DrawDebugTrace.NONE, True)
    return hit.to_tuple()[4].z if hit else 690.0


def build_keys(world):
    """Camera keys every 1/FPS s: position along the polyline at SPEED, yaw blended, head bob while walking."""
    keys = []   # (frame, location, rotation)
    t = 0.0
    frame = 0
    for i, (x, y, yaw, pause) in enumerate(ROUTE):
        if i > 0:
            px, py, pyaw, _ = ROUTE[i - 1]
            dist = math.hypot(x - px, y - py)
            dur = max(dist / SPEED, 0.6)   # a pure turn still takes 0.6 s
            n = max(1, int(round(dur * FPS)))
            for k in range(1, n + 1):
                a = k / n
                s = a * a * (3.0 - 2.0 * a) if dist < 10.0 else a   # ease pure turns
                cx, cy = px + (x - px) * s, py + (y - py) * s
                cyaw = pyaw + (yaw - pyaw) * s
                walking = dist >= 10.0
                tt = t + k / FPS
                bob = BOB * math.sin(2.0 * math.pi * STEP_HZ * tt) if walking else 0.0
                keys.append((frame + k, unreal.Vector(cx, cy, ground(world, cx, cy) + EYE + bob),
                             unreal.Rotator(roll=0.0, pitch=-2.0, yaw=cyaw)))
            frame += n
            t += n / FPS
        else:
            keys.append((0, unreal.Vector(x, y, ground(world, x, y) + EYE), unreal.Rotator(roll=0.0, pitch=-2.0, yaw=yaw)))
        if pause > 0.0:
            n = int(round(pause * FPS))
            last = keys[-1]
            keys.append((frame + n, last[1], last[2]))
            frame += n
            t += pause
    return keys, frame


def build_sequence():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    path = f"{SEQ_DIR}/{SEQ_NAME}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset(SEQ_NAME, SEQ_DIR, unreal.LevelSequence,
                                                                  unreal.LevelSequenceFactoryNew())
    seq.set_display_rate(unreal.FrameRate(FPS, 1))
    seq.set_tick_resolution(unreal.FrameRate(FPS, 1))

    keys, last_frame = build_keys(world)
    seq.set_playback_start(0)
    seq.set_playback_end(last_frame + 1)

    cam = seq.add_spawnable_from_class(unreal.CineCameraActor)
    cam_template = cam.get_object_template()
    # the getter returns None on a spawnable's template object; the property reaches the subobject
    cc = cam_template.get_editor_property("camera_component")
    # 16:9 filmback, 18 mm on 36 mm = 90 deg horizontal, the game's field of view
    fb = cc.get_editor_property("filmback")
    fb.set_editor_property("sensor_width", 36.0)
    fb.set_editor_property("sensor_height", 20.25)
    cc.set_editor_property("filmback", fb)
    cc.set_editor_property("current_focal_length", 18.0)
    focus = cc.get_editor_property("focus_settings")
    focus.set_editor_property("focus_method", unreal.CameraFocusMethod.DISABLE)
    cc.set_editor_property("focus_settings", focus)

    track = cam.add_track(unreal.MovieScene3DTransformTrack)
    section = track.add_section()
    section.set_range(0, last_frame + 1)
    channels = section.get_all_channels()   # loc x/y/z, rot x(roll)/y(pitch)/z(yaw), scale x/y/z
    for frame, loc, rot in keys:
        fn = unreal.FrameNumber(frame)
        for ch, v in ((channels[0], loc.x), (channels[1], loc.y), (channels[2], loc.z),
                      (channels[3], rot.roll), (channels[4], rot.pitch), (channels[5], rot.yaw)):
            ch.add_key(fn, v, interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)

    cut_track = seq.add_track(unreal.MovieSceneCameraCutTrack)
    cut = cut_track.add_section()
    cut.set_range(0, last_frame + 1)
    cut.set_camera_binding_id(seq.get_binding_id(cam))

    unreal.EditorAssetLibrary.save_loaded_asset(seq, False)
    unreal.log(f"render_cp1_walk: sequence {path}, {last_frame + 1} frames ({(last_frame + 1) / FPS:.1f} s)")
    return seq


def render(seq):
    subsystem = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    queue = subsystem.get_queue()
    for job in list(queue.get_jobs()):
        queue.delete_job(job)
    job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
    job.set_editor_property("map", unreal.SoftObjectPath("/Game/KochSimulator/Maps/L_GreyboxTest.L_GreyboxTest"))
    job.set_editor_property("sequence", unreal.SoftObjectPath(seq.get_path_name()))
    job.set_editor_property("job_name", OUT_NAME)

    config = job.get_configuration()
    out = config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
    out.set_editor_property("output_resolution", unreal.IntPoint(1920, 1080))
    out.set_editor_property("output_directory", unreal.DirectoryPath(OUT_DIR))
    out.set_editor_property("file_name_format", OUT_NAME)
    out.set_editor_property("use_custom_frame_rate", True)
    out.set_editor_property("output_frame_rate", unreal.FrameRate(FPS, 1))
    out.set_editor_property("override_existing_output", True)
    config.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
    mp4 = config.find_or_add_setting_by_class(unreal.MoviePipelineMP4EncoderOutput)
    mp4.set_editor_property("include_audio", False)
    # no pawn and no HUD: the camera is the player's eyes
    config.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting)
    aa = config.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
    aa.set_editor_property("engine_warm_up_count", 90)   # streaming, Lumen and TSR history settle before frame 0
    aa.set_editor_property("render_warm_up_frames", True)

    subsystem.render_queue_with_executor(unreal.MoviePipelinePIEExecutor)
    unreal.log(f"render_cp1_walk: rendering to {OUT_DIR}")


render(build_sequence())
