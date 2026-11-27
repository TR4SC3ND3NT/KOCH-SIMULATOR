# -game helper: Hard difficulty, summon Donk (cheat), move him 15-25 m in front of the player on the runtime navmesh.
import time, unreal
S = {"t0": None, "stage": 0, "h": None, "pc": None}
DONK = "/Game/Developers/Azamat/Donk/BP_Enemy_Donk.BP_Enemy_Donk_C"
def log(m): unreal.log("spawn_donk: " + m)
def tick(_dt):
    pc = S["pc"] or next((p for p in unreal.ObjectIterator(unreal.PlayerController) if p.get_world()), None)
    if not pc or not pc.get_controlled_pawn(): return
    S["pc"] = pc; pawn = pc.get_controlled_pawn(); w = pawn.get_world()
    if S["t0"] is None: S["t0"] = time.monotonic()
    t = time.monotonic() - S["t0"]
    if S["stage"] == 0 and t > 1:
        for ds in unreal.ObjectIterator(unreal.KochDifficultySubsystem): ds.set_difficulty(unreal.KochDifficulty.HARD)
        unreal.SystemLibrary.execute_console_command(w, "EnableCheats", pc)
        S["stage"] = 1; log("hard")
    elif S["stage"] == 1 and t > 8:  # give the dynamic navmesh a few seconds to generate
        S["cls"] = unreal.load_object(None, DONK); unreal.SystemLibrary.execute_console_command(w, "summon " + DONK, pc); S["stage"] = 2; log("summoned %s" % S["cls"])
    elif S["stage"] == 2 and t > 9:
        donks = [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.KochEnemyCharacter)]
        here = pawn.get_actor_location(); fwd = pawn.get_actor_forward_vector(); fwd = unreal.Vector(fwd.x, fwd.y, 0).normal()
        spot = None
        for dist in (2000, 1500, 2500, 1000, 700):
            p = unreal.NavigationSystemV1.project_point_to_navigation(w, here + fwd * dist, None, None, unreal.Vector(400, 400, 800))
            if p and abs(p.x) + abs(p.y) > 1: spot = p; break
        for d in donks:
            if spot: d.set_actor_location(spot + unreal.Vector(0, 0, 100), False, True)
            d.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=unreal.MathLibrary.find_look_at_rotation(d.get_actor_location(), here).yaw), True)
        log("donks %d at %s, controller %s, nav spot %s" % (len(donks), donks[0].get_actor_location() if donks else None, donks[0].get_controller() if donks else None, spot))
        S["stage"] = 3; unreal.unregister_slate_post_tick_callback(S["h"])
S["h"] = unreal.register_slate_post_tick_callback(tick)
