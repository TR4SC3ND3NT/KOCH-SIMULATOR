// Anim instance for KOCH enemies: exposes locomotion values (speed, direction, crouch, air, aim) to ABP_KochEnemy_Rifle.
// Values are read from the owning character once per update; no game logic here.

#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "KochEnemyAnimInstance.generated.h"

class ACharacter;

UCLASS()
class KOCHSIMULATOR_API UKochEnemyAnimInstance : public UAnimInstance
{
	GENERATED_BODY()

public:
	/** Horizontal speed divided by the actor scale (cm/s): the speed a full-size body would need for the same stride.
	 *  Drives the Speed axis of the locomotion blend spaces, so a 0.75-scale enemy does not slide its feet. */
	UPROPERTY(BlueprintReadOnly, Category = "Koch|Locomotion")
	float GroundSpeed = 0.0f;

	/** Speeds the clips up once GroundSpeed passes the fastest blend-space sample (blend spaces clamp, they do not extrapolate). */
	UPROPERTY(BlueprintReadOnly, Category = "Koch|Locomotion")
	float LocomotionPlayRate = 1.0f;

	/** Speed of the fastest standing / crouched sample in the blend spaces (cm/s). */
	UPROPERTY(EditDefaultsOnly, Category = "Koch|Locomotion", meta = (ClampMin = 1, Units = "cm/s"))
	float StandTopSampleSpeed = 450.0f;

	UPROPERTY(EditDefaultsOnly, Category = "Koch|Locomotion", meta = (ClampMin = 1, Units = "cm/s"))
	float CrouchTopSampleSpeed = 140.0f;

	/** Movement direction relative to facing (degrees, -180..180, 0 = forward, 90 = right). */
	UPROPERTY(BlueprintReadOnly, Category = "Koch|Locomotion")
	float Direction = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Koch|Locomotion")
	bool bIsCrouching = false;

	UPROPERTY(BlueprintReadOnly, Category = "Koch|Locomotion")
	bool bIsInAir = false;

	/** Aim pitch relative to the body (degrees, + = up), from the controller's view (AI focus). */
	UPROPERTY(BlueprintReadOnly, Category = "Koch|Aim")
	float AimPitch = 0.0f;

	/** Aim yaw relative to the body (degrees). */
	UPROPERTY(BlueprintReadOnly, Category = "Koch|Aim")
	float AimYaw = 0.0f;

protected:
	virtual void NativeInitializeAnimation() override;
	virtual void NativeUpdateAnimation(float DeltaSeconds) override;

private:
	TWeakObjectPtr<ACharacter> Character;
};
