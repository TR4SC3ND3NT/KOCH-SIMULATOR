import unreal, time, os, builtins, math, shutil
OUT=os.path.join(unreal.Paths.project_saved_dir(), "EnemyCaps")
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
sun=[a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.DirectionalLight)][0]
d=sun.get_actor_forward_vector(); to_light=unreal.Vector(-d.x,-d.y,0).normal(); face_yaw=math.degrees(math.atan2(to_light.y,to_light.x))
studio={}
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
    lbl=a.get_actor_label()
    if lbl.startswith("Studio_"): studio[lbl[7:]]=a
for e,dd in studio.items():
    c=dd.get_controller() if hasattr(dd,'get_controller') else None
    if c: c.un_possess()
cam=studio["Camera"]; cc=cam.get_editor_property("capture_component2d")
rt=unreal.RenderingLibrary.create_render_target2d(w, 480, 600, unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(0,0,0,1))
cc.set_editor_property("texture_target", rt); cc.set_editor_property("capture_every_frame", False); cc.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR); cc.set_editor_property("fov_angle", 30.0)
L=unreal.load_asset; R="/Game/Characters/Heroes/Mannequin/Animations/"
seq={"rifle":(L(R+"Locomotion/Rifle/MM_Rifle_Idle_Hipfire"),L(R+"Locomotion/Rifle/MM_Rifle_Jog_Fwd")),"pistol":(L(R+"Locomotion/Pistol/MM_Pistol_Idle_Hipfire"),L(R+"Locomotion/Pistol/MM_Pistol_Jog_Fwd"))}
hit=L(R+"Actions/AM_MM_HitReact_Front_Lgt_01")
E=[("Donk","rifle"),("Guard","pistol"),("Interceptor","rifle"),("Flanker","rifle"),("Heavy","rifle")]
ANIMS=[("idle",2.0),("jog",1.6),("fire",1.6),("reload",2.4),("hit",1.0)]
FPS=12.0
jobs=[(e,k,a,du) for e,k in E for a,du in ANIMS]
st={"j":-1,"t0":0,"n":0,"next":0,"lastfire":0}
side=unreal.Vector(-to_light.y, to_light.x, 0)
def setup(e,kind,anim):
    dd=studio[e]; m=dd.get_editor_property("mesh")
    dd.set_actor_rotation(unreal.Rotator(yaw=face_yaw), True)
    loc=dd.get_actor_location(); half=dd.get_editor_property("capsule_component").get_scaled_capsule_half_height()
    dist=half*2*1.9; tgt=unreal.Vector(loc.x, loc.y, loc.z+half*0.1)
    p=tgt+to_light*dist+side*(dist*0.35); cam.set_actor_location(p, False, True)
    cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(p, tgt), True)
    if anim in ("idle","jog"):
        m.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE); m.play_animation(seq[kind][0 if anim=="idle" else 1], True)
    else:
        m.set_animation_mode(unreal.AnimationMode.ANIMATION_BLUEPRINT)
    os.makedirs("%s/%s/%s"%(OUT,e,anim), exist_ok=True)
def tick(dt):
    try:
        now=time.monotonic()
        if st["j"]<0 or now-st["t0"]>=jobs[st["j"]][3]:
            st["j"]+=1
            if st["j"]>=len(jobs):
                unreal.unregister_slate_post_tick_callback(builtins._cap); open(OUT+"/DONE","w").write("ok"); return
            e,k,a,du=jobs[st["j"]]; setup(e,k,a); st.update(t0=now+0.4,n=0,next=now+0.4,lastfire=0); return
        e,k,a,du=jobs[st["j"]]
        if now<st["t0"]: return
        dd=studio[e]; ai=dd.get_editor_property("mesh").get_anim_instance()
        if a=="fire" and now-st["lastfire"]>(0.35 if k=="pistol" else 0.12): ai.montage_play(dd.get_editor_property("fire_montage")); st["lastfire"]=now
        if a=="reload" and st["n"]==0 and not ai.montage_is_playing(dd.get_editor_property("reload_montage")): ai.montage_play(dd.get_editor_property("reload_montage"))
        if a=="hit" and st["n"]==0: ai.montage_play(hit)
        if now>=st["next"]:
            cc.capture_scene(); unreal.RenderingLibrary.export_render_target(w, rt, "%s/%s/%s"%(OUT,e,a), "f%03d.png"%st["n"]); st["n"]+=1; st["next"]+=1.0/FPS
    except Exception as ex:
        open(OUT+"/ERR","w").write(str(ex)); unreal.unregister_slate_post_tick_callback(builtins._cap)
for e in ["Donk","Guard","Interceptor","Flanker","Heavy"]: shutil.rmtree(OUT+"/"+e, ignore_errors=True)
for f in ("DONE","ERR"):
    if os.path.exists(OUT+"/"+f): os.remove(OUT+"/"+f)
builtins._cap=unreal.register_slate_post_tick_callback(tick); print("recording", len(jobs))
