// View recoil for the player: each shot kicks the aim up, most of the climb settles back unless the player pulls down first.
// Owner: AShooterCharacter (fed by AShooterWeapon through IShooterWeaponHolder::AddWeaponKick). Also holds the fire camera shake.
// Model after CrystalVapor/UE5-CrystalRecoil (MIT, github.com/CrystalVapor/UE5-CrystalRecoil): persistent aim kick,
// delayed partial recovery, player compensation counted against the recovery. Re-written here, no code copied.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Shakes/DefaultCameraShakeBase.h"
#include "Combat/KochCombatTypes.h"
#include "KochRecoilComponent.generated.h"

/** Short, small Perlin shake played per shot. Rotation stays under half a degree (motion sickness). */
UCLASS()
class KOCHSIMULATOR_API UKochFireCameraShake : public UDefaultCameraShakeBase
{
	GENERATED_BODY()

public:

	UKochFireCameraShake(const FObjectInitializer& ObjectInitializer);
};

UCLASS(ClassGroup=(Koch), meta=(BlueprintSpawnableComponent))
class KOCHSIMULATOR_API UKochRecoilComponent : public UActorComponent
{
	GENERATED_BODY()

public:

	UKochRecoilComponent();

	/** One shot fired: queues the kick and plays the fire shake. */
	void AddKick(const FKochRecoilSpec& Recoil);

	/** Ticks only while a kick or its recovery is in progress. */
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

protected:

	/** How fast a queued kick reaches the view (1/s). 30: most of it within two frames at 60 fps, never a one-frame snap. */
	UPROPERTY(EditAnywhere, Category="Recoil", meta=(ClampMin=1))
	float KickSpeed = 30.0f;

	/** Camera shake per shot (none: no shake). */
	UPROPERTY(EditAnywhere, Category="Recoil")
	TSubclassOf<UCameraShakeBase> FireShake;

	/** Scales the fire shake; the place for a "camera motion" setting. 0 turns it off. */
	UPROPERTY(EditAnywhere, Category="Recoil", meta=(ClampMin=0, ClampMax=2))
	float ShakeScale = 1.0f;

private:

	void Stop();

	/** Degrees still to be added to the view: X pitch (up), Y yaw. */
	FVector2D PendingKick = FVector2D::ZeroVector;

	/** Degrees of applied kick that will be taken back. */
	FVector2D Recoverable = FVector2D::ZeroVector;

	/** Control rotation as this component last wrote it; the difference to the next frame is the player's own input. */
	FRotator LastControlRotation = FRotator::ZeroRotator;

	bool bHasLastControlRotation = false;

	/** Seconds since the last shot. */
	float TimeSinceShot = 0.0f;

	/** Recovery settings of the weapon that fired last. */
	float RecoveryFraction = 0.0f;
	float RecoveryDelay = 0.0f;
	float RecoverySpeed = 1.0f;
};
