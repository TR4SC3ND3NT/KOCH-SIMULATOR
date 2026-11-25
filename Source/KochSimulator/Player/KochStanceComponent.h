// Player stance: aim down sights (zoom, slower look and walk, tighter spread), sprint with stamina, crouch.
// Owner: AShooterCharacter, which forwards input setup, look scaling, spread scaling and weapon state to it.
// Speeds follow grounded shooters (Insurgency-style): jog by default, sprint is a commitment that drops the aim.
// Not here yet: sight alignment and weapon sway/bob (need the first-person anim Blueprint), stamina HUD.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "KochStanceComponent.generated.h"

class ACharacter;
class UCameraComponent;
class UCharacterMovementComponent;
class UEnhancedInputComponent;
class UEnhancedInputLocalPlayerSubsystem;
class UInputAction;
class UInputMappingContext;
class USceneComponent;

UCLASS(ClassGroup=(Koch), meta=(BlueprintSpawnableComponent))
class KOCHSIMULATOR_API UKochStanceComponent : public UActorComponent
{
	GENERATED_BODY()

public:

	UKochStanceComponent();

	/** Binds aim / sprint / crouch and adds the mapping context. Call from the owner's SetupPlayerInputComponent. */
	void SetupInput(UEnhancedInputComponent* Input);

	/** Also usable from UI or touch controls. */
	UFUNCTION(BlueprintCallable, Category="Stance")
	void StartAim();

	UFUNCTION(BlueprintCallable, Category="Stance")
	void StopAim();

	UFUNCTION(BlueprintCallable, Category="Stance")
	void StartSprint();

	UFUNCTION(BlueprintCallable, Category="Stance")
	void StopSprint();

	UFUNCTION(BlueprintCallable, Category="Stance")
	void ToggleCrouch();

	/** Aiming needs a weapon in hand; the owner reports draw / holster / death here. */
	void SetWeaponReady(bool bReady);

	/** A shot was fired: breaks the sprint for SprintLockAfterShot seconds. */
	void NotifyFired();

	UFUNCTION(BlueprintPure, Category="Stance")
	bool IsAiming() const { return bAiming; }

	UFUNCTION(BlueprintPure, Category="Stance")
	bool IsSprinting() const { return bSprinting; }

	/** 0 at the hip, 1 fully aimed; blends over about 0.2 s. */
	float GetAimAlpha() const { return AimAlpha; }

	/** 0 (exhausted) to 1 (rested). */
	UFUNCTION(BlueprintPure, Category="Stance")
	float GetStamina() const { return Stamina; }

	/** Multiplier for the weapon's bullet spread in the current stance. */
	float GetSpreadScale() const;

	/** Multiplier for look input: keeps the on-screen turn speed constant while zoomed. */
	float GetLookScale() const;

	/** Ticks only while something is changing: aim blend, crouch blend, sprint, stamina regeneration. */
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

protected:

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	/** Optional input assets. Any left empty is created in code with the default keys:
	 *  aim = right mouse / left trigger, sprint = left shift / left stick click, crouch = left ctrl, C / right stick click. */
	UPROPERTY(EditAnywhere, Category="Input")
	TObjectPtr<UInputAction> AimAction;

	UPROPERTY(EditAnywhere, Category="Input")
	TObjectPtr<UInputAction> SprintAction;

	UPROPERTY(EditAnywhere, Category="Input")
	TObjectPtr<UInputAction> CrouchAction;

	UPROPERTY(EditAnywhere, Category="Input")
	TObjectPtr<UInputMappingContext> MappingContext;

	/** Above the template contexts (0), so left shift sprints instead of swapping weapons. */
	UPROPERTY(EditAnywhere, Category="Input")
	int32 MappingPriority = 1;

	UPROPERTY(EditAnywhere, Category="Movement", meta=(ClampMin=0, Units="cm/s"))
	float JogSpeed = 400.0f;

	UPROPERTY(EditAnywhere, Category="Movement", meta=(ClampMin=0, Units="cm/s"))
	float SprintSpeed = 620.0f;

	UPROPERTY(EditAnywhere, Category="Movement", meta=(ClampMin=0, Units="cm/s"))
	float CrouchSpeed = 180.0f;

	/** Walk speed multiplier while aiming. */
	UPROPERTY(EditAnywhere, Category="Movement", meta=(ClampMin=0, ClampMax=1))
	float AimSpeedScale = 0.55f;

	/** cm/s^2. Lower than the template's 2048: the body has weight. */
	UPROPERTY(EditAnywhere, Category="Movement", meta=(ClampMin=0))
	float Acceleration = 1500.0f;

	UPROPERTY(EditAnywhere, Category="Movement", meta=(ClampMin=0))
	float BrakingDeceleration = 1800.0f;

	/** Seconds of sprint from rested to exhausted. */
	UPROPERTY(EditAnywhere, Category="Stamina", meta=(ClampMin=0.1, Units="s"))
	float SprintSeconds = 10.0f;

	/** Seconds from exhausted to rested. */
	UPROPERTY(EditAnywhere, Category="Stamina", meta=(ClampMin=0.1, Units="s"))
	float StaminaRegenSeconds = 6.0f;

	/** Seconds after a sprint before stamina starts to return. */
	UPROPERTY(EditAnywhere, Category="Stamina", meta=(ClampMin=0, Units="s"))
	float StaminaRegenDelay = 1.0f;

	/** Stamina needed to start a sprint; stops stutter-sprinting on an empty bar. */
	UPROPERTY(EditAnywhere, Category="Stamina", meta=(ClampMin=0, ClampMax=1))
	float MinStaminaToSprint = 0.2f;

	UPROPERTY(EditAnywhere, Category="Stamina", meta=(ClampMin=0, Units="s"))
	float SprintLockAfterShot = 0.35f;

	/** World field of view while aiming (degrees). The hip value is the camera's own. Keep the change under ~25. */
	UPROPERTY(EditAnywhere, Category="Aim", meta=(ClampMin=10, ClampMax=120, Units="Degrees"))
	float AimFieldOfView = 68.0f;

	/** Field of view of the first-person arms and weapon while aiming. */
	UPROPERTY(EditAnywhere, Category="Aim", meta=(ClampMin=10, ClampMax=120, Units="Degrees"))
	float AimFirstPersonFieldOfView = 58.0f;

	/** Aim in / out rate (1/s): 12 is about 0.2 s. */
	UPROPERTY(EditAnywhere, Category="Aim", meta=(ClampMin=1))
	float AimBlendSpeed = 12.0f;

	UPROPERTY(EditAnywhere, Category="Spread", meta=(ClampMin=0))
	float AimSpreadScale = 0.15f;

	UPROPERTY(EditAnywhere, Category="Spread", meta=(ClampMin=0))
	float MovingSpreadScale = 1.7f;

	UPROPERTY(EditAnywhere, Category="Spread", meta=(ClampMin=0))
	float AirborneSpreadScale = 3.0f;

	UPROPERTY(EditAnywhere, Category="Spread", meta=(ClampMin=0))
	float CrouchSpreadScale = 0.8f;

	/** Ground speed above which the moving spread applies. */
	UPROPERTY(EditAnywhere, Category="Spread", meta=(ClampMin=0, Units="cm/s"))
	float MovingSpeedThreshold = 120.0f;

	/** Capsule half height while crouched (standing: 96). */
	UPROPERTY(EditAnywhere, Category="Crouch", meta=(ClampMin=34, Units="cm"))
	float CrouchedHalfHeight = 60.0f;

	/** How far the view drops while crouched. The template's first-person rig has no crouch pose, so the rig is lowered. */
	UPROPERTY(EditAnywhere, Category="Crouch", meta=(ClampMin=0, Units="cm"))
	float CrouchEyeDrop = 48.0f;

	/** Crouch down / stand up rate (1/s). */
	UPROPERTY(EditAnywhere, Category="Crouch", meta=(ClampMin=1))
	float CrouchBlendSpeed = 9.0f;

private:

	/** Re-evaluates aim and sprint from what the player holds and what the stance allows; applies walk speeds. */
	void UpdateState();

	bool CanSprint() const;

	UPROPERTY(Transient)
	TObjectPtr<ACharacter> Character;

	UPROPERTY(Transient)
	TObjectPtr<UCharacterMovementComponent> Movement;

	UPROPERTY(Transient)
	TObjectPtr<UCameraComponent> Camera;

	/** First-person rig the camera rides on; lowered for the crouch. */
	UPROPERTY(Transient)
	TObjectPtr<USceneComponent> ViewRig;

	TWeakObjectPtr<UEnhancedInputLocalPlayerSubsystem> InputSubsystem;

	FVector ViewRigRestLocation = FVector::ZeroVector;
	float HipFieldOfView = 90.0f;
	float HipFirstPersonFieldOfView = 70.0f;

	/** What the player is holding down. */
	bool bWantsAim = false;
	bool bWantsSprint = false;

	/** What is actually happening. */
	bool bAiming = false;
	bool bSprinting = false;
	bool bWeaponReady = false;

	/** 0 hip, 1 fully aimed. */
	float AimAlpha = 0.0f;

	/** 0 standing, 1 fully crouched. */
	float CrouchAlpha = 0.0f;

	float Stamina = 1.0f;

	/** Seconds since the sprint ended (stamina regeneration delay). */
	float TimeSinceSprint = 0.0f;

	/** Seconds left during which sprinting is refused (after a shot). */
	float SprintLock = 0.0f;
};
