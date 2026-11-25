// First-person weapon motion without touching the anim Blueprints: sight alignment when aiming, look sway, walk bob,
// landing dip, breathing and a visual kick per shot. Owner: AShooterCharacter.
// How: the template camera rides the first-person rig's head socket, so arms and weapon cannot be offset by moving the
// rig. Instead the camera is shifted a few centimetres inside the rig; on screen that is the weapon moving the opposite
// way, while the world view shifts by the same few centimetres (not noticeable). Translation only: rotating the camera
// would swing the world, which is recoil's job (UKochRecoilComponent).
// Sway and bob amplitudes follow the usual motion-comfort advice: on the weapon, not the camera, a few centimetres at most.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "KochViewMotionComponent.generated.h"

class ACharacter;
class AShooterWeapon;
class UCameraComponent;
class UKochStanceComponent;
struct FHitResult;

UCLASS(ClassGroup=(Koch), meta=(BlueprintSpawnableComponent))
class KOCHSIMULATOR_API UKochViewMotionComponent : public UActorComponent
{
	GENERATED_BODY()

public:

	UKochViewMotionComponent();

	/** Weapon in hand (null: none or holstered). Motion runs only with a weapon out, then blends back to rest. */
	void SetWeapon(AShooterWeapon* Weapon);

	/** A shot was fired: the weapon jolts back toward the eye. */
	void NotifyFired();

	/** Ticks while a weapon is out or an offset is still settling; after the first-person rig so its sockets are current. */
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

protected:

	virtual void BeginPlay() override;

	/** Scales sway, bob, landing and breathing (not the sight alignment). The place for a "weapon motion" setting. */
	UPROPERTY(EditAnywhere, Category="Motion", meta=(ClampMin=0, ClampMax=2))
	float MotionScale = 1.0f;

	/** Sway, bob and landing while fully aimed, as a share of the hip amount. */
	UPROPERTY(EditAnywhere, Category="Motion", meta=(ClampMin=0, ClampMax=1))
	float AimMotionScale = 0.25f;

	/** While aiming, how far in front of the eye the sight sits (cm). 0 keeps the hip distance. */
	UPROPERTY(EditAnywhere, Category="Aim", meta=(ClampMin=0, Units="cm"))
	float AimEyeRelief = 0.0f;

	/** Weapon lag per degree-per-second of turning (cm). */
	UPROPERTY(EditAnywhere, Category="Sway", meta=(ClampMin=0))
	float SwayPerDegreePerSecond = 0.012f;

	UPROPERTY(EditAnywhere, Category="Sway", meta=(ClampMin=0, Units="cm"))
	float MaxSway = 1.6f;

	/** Spring that carries the sway: Hz and damping ratio (under 1 overshoots a little, which reads as weight). */
	UPROPERTY(EditAnywhere, Category="Sway", meta=(ClampMin=0.1))
	float SwayFrequency = 6.0f;

	UPROPERTY(EditAnywhere, Category="Sway", meta=(ClampMin=0.1, ClampMax=2))
	float SwayDamping = 0.6f;

	/** Side-to-side and up-down bob at JogReferenceSpeed (cm). */
	UPROPERTY(EditAnywhere, Category="Bob", meta=(ClampMin=0, Units="cm"))
	float BobSide = 0.45f;

	UPROPERTY(EditAnywhere, Category="Bob", meta=(ClampMin=0, Units="cm"))
	float BobUp = 0.35f;

	/** Ground covered by one left-right bob cycle (two steps). */
	UPROPERTY(EditAnywhere, Category="Bob", meta=(ClampMin=10, Units="cm"))
	float StrideLength = 190.0f;

	/** Ground speed at which the bob has the amplitudes above; it scales with speed up to MaxBobScale. */
	UPROPERTY(EditAnywhere, Category="Bob", meta=(ClampMin=1, Units="cm/s"))
	float JogReferenceSpeed = 400.0f;

	UPROPERTY(EditAnywhere, Category="Bob", meta=(ClampMin=0))
	float MaxBobScale = 1.7f;

	/** Weapon dip for a hard landing (cm), reached at LandingReferenceSpeed of fall speed. */
	UPROPERTY(EditAnywhere, Category="Landing", meta=(ClampMin=0, Units="cm"))
	float LandingDip = 2.5f;

	UPROPERTY(EditAnywhere, Category="Landing", meta=(ClampMin=1, Units="cm/s"))
	float LandingReferenceSpeed = 700.0f;

	/** Up-down drift of a held weapon (cm) and its rate (Hz). */
	UPROPERTY(EditAnywhere, Category="Breathing", meta=(ClampMin=0, Units="cm"))
	float BreathAmplitude = 0.12f;

	UPROPERTY(EditAnywhere, Category="Breathing", meta=(ClampMin=0))
	float BreathFrequency = 0.25f;

	/** How far the weapon jolts toward the eye per shot (cm). */
	UPROPERTY(EditAnywhere, Category="Fire", meta=(ClampMin=0, Units="cm"))
	float FireKick = 1.0f;

	/** Spring of the jolt, the landing dip and the return to rest: Hz. */
	UPROPERTY(EditAnywhere, Category="Fire", meta=(ClampMin=0.1))
	float ImpulseFrequency = 5.0f;

private:

	UFUNCTION()
	void OnLanded(const FHitResult& Hit);

	UPROPERTY(Transient)
	TObjectPtr<ACharacter> Character;

	UPROPERTY(Transient)
	TObjectPtr<UCameraComponent> Camera;

	UPROPERTY(Transient)
	TObjectPtr<UKochStanceComponent> Stance;

	UPROPERTY(Transient)
	TObjectPtr<AShooterWeapon> CurrentWeapon;

	/** Camera location inside the rig as the template placed it. */
	FVector RestLocation = FVector::ZeroVector;

	/** 0 with no weapon, 1 with one in hand; everything but the rest pose is scaled by it. */
	float WeaponAlpha = 0.0f;

	/** Sway offset and its rate, view space (Y right, Z up), cm. */
	FVector2D Sway = FVector2D::ZeroVector;
	FVector2D SwayRate = FVector2D::ZeroVector;

	/** Jolt (X, toward the eye) and landing dip (Z) and their rates, cm. */
	FVector2D Impulse = FVector2D::ZeroVector;
	FVector2D ImpulseRate = FVector2D::ZeroVector;

	/** Radians along the stride cycle. */
	float BobPhase = 0.0f;

	/** 0 standing still, 1 at jog speed; smoothed so the bob fades in and out. */
	float BobAmount = 0.0f;

	float BreathPhase = 0.0f;

	FRotator LastViewRotation = FRotator::ZeroRotator;
	bool bHasLastViewRotation = false;
};
