# Standalone perf capture (R4 -> everyone): warm up, 30 s FPS chart, then stat unit/gpu screenshot + ProfileGPU, quit.
# Profile in -game, not PIE (the editor costs GPU ms and VRAM). Results: log (FPS chart summary, ProfileGPU tree),
# Saved/Screenshots (shot with the stat overlay), Saved/Profiling/FPSChartStats.
# Run: UnrealEditor.exe KochSimulator.uproject /Game/KochSimulator/Maps/L_GreyboxTest -game -dx12 -windowed
#        -ResX=1920 -ResY=1080 -ExecCmds="py Scripts/Unreal/perf_capture.py" [-dpcvars=r.Lumen.HardwareRayTracing=1]
# Env: KOCH_PERF_YAW (deg, camera heading; default 20 = gate plaza towards the trees and block A).
import os
import time

import unreal

WARMUP_S, CHART_S = 20.0, 30.0
YAW = float(os.environ.get("KOCH_PERF_YAW", "20"))
# (seconds after start, console commands); FPS chart runs with no stat overlay so the overlay's cost is excluded
STEPS = [
    (WARMUP_S, ["r.VSync 0", "t.MaxFPS 0", "r.ProfileGPU.ShowUI 0", "startfpschart"]),
    (WARMUP_S + CHART_S, ["stopfpschart", "stat unit", "stat gpu"]),
    (WARMUP_S + CHART_S + 4, ["shot showui", "ProfileGPU"]),
    (WARMUP_S + CHART_S + 8, ["quit"]),
]
state = {"t0": None, "i": 0, "handle": None, "pc": None}


def tick(_dt):
    # ObjectIterator walks every UObject: do it until the controller exists, then cache (it cost game-thread ms per frame)
    pc = state["pc"]
    if pc is None:
        pc = next((p for p in unreal.ObjectIterator(unreal.PlayerController) if p.get_world()), None)
        if pc is None:
            return
        state["pc"] = pc
    if state["t0"] is None:
        state["t0"] = time.monotonic()
        pc.set_ignore_move_input(True)   # a mouse over the window must not move the measured view
        pc.set_ignore_look_input(True)
        pc.set_control_rotation(unreal.Rotator(roll=0.0, pitch=-5.0, yaw=YAW))
        unreal.log(f"perf_capture: armed, yaw {YAW}")
    t = time.monotonic() - state["t0"]
    while state["i"] < len(STEPS) and t >= STEPS[state["i"]][0]:
        for cmd in STEPS[state["i"]][1]:
            unreal.log(f"perf_capture: {cmd}")
            # APlayerController::ConsoleCommand is not script-exposed in 5.8; this routes through the same player
            unreal.SystemLibrary.execute_console_command(pc.get_world(), cmd, pc)
        state["i"] += 1
    if state["i"] == len(STEPS) and state["handle"] is not None:
        unreal.unregister_slate_post_tick_callback(state["handle"])
        state["handle"] = None


state["handle"] = unreal.register_slate_post_tick_callback(tick)
