# UE 5.8 editor script (R4 -> everyone): creates/opens the greybox render test level /Game/KochSimulator/Maps/L_GreyboxTest
# (World Partition) with a physically based outdoor light rig, so import_greybox.py has a level to place into and
# Lumen/VSM can be profiled. Idempotent: actors are found by label and reconfigured, never duplicated.
# Light values: sun 100 000 lux (clear-sky noon), auto exposure clamped to EV100 10..15, bias -0.5, per Epic's
# "Using Physical Lighting Units" (dev.epicgames.com/documentation/en-us/unreal-engine/using-physical-lighting-units-in-unreal-engine).
# Run (Output Log, Cmd = Python): py "<repo>/Scripts/Unreal/setup_test_level.py"
import unreal

LEVEL = "/Game/KochSimulator/Maps/L_GreyboxTest"
SUN_LUX = 100000.0
# Bishkek (42.8566 N, 74.679 E) 2026-09-25 15:00 UTC+6, NOAA solar position: elevation 37.8, azimuth 221.7 (SW).
# UE: +X east, +Y south (decisions.md world frame), so light yaw = azimuth + 90 and pitch = -elevation.
SUN_ROT = unreal.Rotator(roll=0.0, pitch=-37.8, yaw=311.7)
EV100_MIN, EV100_MAX = 10.0, 15.0
EXPOSURE_BIAS = -0.5   # A/B in PIE 2026-10-26: 8..15/0 washed out sunlit paving, 12..15/-1 crushed the shade


def get_or_spawn(eas, cls, label, loc=unreal.Vector(0, 0, 0), rot=unreal.Rotator()):
    for a in eas.get_all_level_actors():
        if isinstance(a, cls) and a.get_actor_label() == label:
            return a
    a = eas.spawn_actor_from_class(cls, loc, rot)
    a.set_actor_label(label)
    a.set_folder_path("Lighting")
    return a


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL):
        les.load_level(LEVEL)
    elif not les.new_level(LEVEL, True):
        raise RuntimeError(f"setup_test_level: could not create {LEVEL}")
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    sun = get_or_spawn(eas, unreal.DirectionalLight, "Sun", unreal.Vector(0, 0, 5000), SUN_ROT)
    sun.set_actor_rotation(SUN_ROT, False)
    lc = sun.get_editor_property("directional_light_component")
    lc.set_mobility(unreal.ComponentMobility.MOVABLE)
    lc.set_intensity(SUN_LUX)
    lc.set_editor_property("atmosphere_sun_light", True)

    get_or_spawn(eas, unreal.SkyAtmosphere, "SkyAtmosphere")

    sky = get_or_spawn(eas, unreal.SkyLight, "SkyLight", unreal.Vector(0, 0, 3000))
    sc = sky.get_editor_property("light_component")
    sc.set_mobility(unreal.ComponentMobility.MOVABLE)
    sc.set_editor_property("real_time_capture", True)

    get_or_spawn(eas, unreal.ExponentialHeightFog, "HeightFog", unreal.Vector(0, 0, 500))

    ppv = get_or_spawn(eas, unreal.PostProcessVolume, "PPV_Global")
    ppv.set_editor_property("unbound", True)
    s = ppv.get_editor_property("settings")
    for prop, value in (("auto_exposure_method", unreal.AutoExposureMethod.AEM_HISTOGRAM),
                        ("auto_exposure_min_brightness", EV100_MIN), ("auto_exposure_max_brightness", EV100_MAX),
                        ("auto_exposure_bias", EXPOSURE_BIAS)):
        s.set_editor_property("override_" + prop, True)
        s.set_editor_property(prop, value)
    ppv.set_editor_property("settings", s)

    les.save_current_level()
    unreal.log(f"setup_test_level: {LEVEL} ready")


main()
