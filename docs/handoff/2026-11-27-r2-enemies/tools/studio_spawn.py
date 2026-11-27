import unreal
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith(("Shot_","Studio_")): a.destroy_actor()
E=[("Donk","/Game/Developers/Azamat/Donk/BP_Enemy_Donk.BP_Enemy_Donk_C"),("Guard","/Game/Developers/Azamat/Enemies/Guard/BP_Enemy_Guard.BP_Enemy_Guard_C"),("Interceptor","/Game/Developers/Azamat/Enemies/Interceptor/BP_Enemy_Interceptor.BP_Enemy_Interceptor_C"),("Flanker","/Game/Developers/Azamat/Enemies/Flanker/BP_Enemy_Flanker.BP_Enemy_Flanker_C"),("Heavy","/Game/Developers/Azamat/Enemies/Heavy/BP_Enemy_Heavy.BP_Enemy_Heavy_C")]
for i,(n,c) in enumerate(E):
    a=eas.spawn_actor_from_class(unreal.load_object(None,c), unreal.Vector(-3000, i*800, 120), unreal.Rotator(yaw=0)); a.set_actor_label("Studio_"+n)
cap=eas.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(-2700,0,120)); cap.set_actor_label("Studio_Camera")
s=unreal.get_default_object(unreal.load_class(None,"/Script/UnrealEd.EditorPerformanceSettings")); s.set_editor_property("bThrottleCPUWhenNotForeground", False)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_play_simulate(); print("sim")
