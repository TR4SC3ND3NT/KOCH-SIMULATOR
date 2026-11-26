// See KochEnemyAnimInstance.h.

#include "KochEnemyAnimInstance.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"

void UKochEnemyAnimInstance::NativeInitializeAnimation()
{
	Super::NativeInitializeAnimation();
	Character = Cast<ACharacter>(TryGetPawnOwner());
}

void UKochEnemyAnimInstance::NativeUpdateAnimation(float DeltaSeconds)
{
	Super::NativeUpdateAnimation(DeltaSeconds);

	const ACharacter* Owner = Character.Get();
	if (!Owner)
	{
		Character = Cast<ACharacter>(TryGetPawnOwner());
		return;
	}

	const FVector Velocity = Owner->GetVelocity();
	GroundSpeed = Velocity.Size2D();

	const FRotator ActorRotation = Owner->GetActorRotation();
	Direction = (GroundSpeed > 1.0f)
		? FRotator::NormalizeAxis(Velocity.Rotation().Yaw - ActorRotation.Yaw)
		: 0.0f;

	if (const UCharacterMovementComponent* Move = Owner->GetCharacterMovement())
	{
		bIsCrouching = Move->IsCrouching();
		bIsInAir = Move->IsFalling();
	}

	// Base aim rotation = controller view (AI: towards the focus actor), so this is where the gun should point.
	const FRotator AimDelta = (Owner->GetBaseAimRotation() - ActorRotation).GetNormalized();
	AimPitch = AimDelta.Pitch;
	AimYaw = AimDelta.Yaw;
}
