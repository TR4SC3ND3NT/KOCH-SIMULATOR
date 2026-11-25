// See KochRecoilComponent.h.

#include "Player/KochRecoilComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Shakes/PerlinNoiseCameraShakePattern.h"

UKochFireCameraShake::UKochFireCameraShake(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	// full-auto fire restarts the one instance instead of stacking ten a second
	bSingleInstance = true;

	UPerlinNoiseCameraShakePattern* Pattern = CastChecked<UPerlinNoiseCameraShakePattern>(GetRootShakePattern());
	Pattern->Duration = 0.14f;
	Pattern->BlendInTime = 0.01f;
	Pattern->BlendOutTime = 0.10f;

	// degrees
	Pattern->Pitch.Amplitude = 0.30f;
	Pattern->Pitch.Frequency = 18.0f;
	Pattern->Yaw.Amplitude = 0.20f;
	Pattern->Yaw.Frequency = 14.0f;
	Pattern->Roll.Amplitude = 0.40f;
	Pattern->Roll.Frequency = 12.0f;

	// cm along the view: the shove of the stock
	Pattern->X.Amplitude = 0.5f;
	Pattern->X.Frequency = 20.0f;
}

UKochRecoilComponent::UKochRecoilComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = false;

	FireShake = UKochFireCameraShake::StaticClass();
}

void UKochRecoilComponent::AddKick(const FKochRecoilSpec& Recoil)
{
	const APawn* Pawn = Cast<APawn>(GetOwner());
	APlayerController* Player = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
	if (!Player)
	{
		return;
	}

	PendingKick.X += Recoil.PitchKick;
	PendingKick.Y += FMath::FRandRange(-Recoil.YawKick, Recoil.YawKick);
	RecoveryFraction = Recoil.RecoveryFraction;
	RecoveryDelay = Recoil.RecoveryDelay;
	RecoverySpeed = Recoil.RecoverySpeed;
	TimeSinceShot = 0.0f;

	if (!IsComponentTickEnabled())
	{
		bHasLastControlRotation = false;
		SetComponentTickEnabled(true);
	}

	const float Scale = ShakeScale * Recoil.ShakeScale;
	if (FireShake && Scale > 0.0f && Player->PlayerCameraManager)
	{
		Player->PlayerCameraManager->StartCameraShake(FireShake, Scale);
	}
}

void UKochRecoilComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	const APawn* Pawn = Cast<APawn>(GetOwner());
	APlayerController* Player = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
	if (!Player)
	{
		Stop();
		return;
	}

	FRotator Rotation = Player->GetControlRotation();

	// whatever the player did since the last write counts against the recovery: pulling down against the climb is
	// their own recovery, and giving it back a second time would drag the aim below the target
	if (bHasLastControlRotation)
	{
		const float PlayerPitch = FRotator::NormalizeAxis(Rotation.Pitch - LastControlRotation.Pitch);
		const float PlayerYaw = FRotator::NormalizeAxis(Rotation.Yaw - LastControlRotation.Yaw);
		if (Recoverable.X > 0.0 && PlayerPitch < 0.0f)
		{
			Recoverable.X = FMath::Max(0.0, Recoverable.X + PlayerPitch);
		}
		if (Recoverable.Y * PlayerYaw < 0.0)
		{
			Recoverable.Y = FMath::Sign(Recoverable.Y) * FMath::Max(0.0, FMath::Abs(Recoverable.Y) - FMath::Abs(PlayerYaw));
		}
	}

	TimeSinceShot += DeltaTime;

	// frame-rate independent exponential approach
	FVector2D Step = PendingKick * (1.0 - FMath::Exp(-KickSpeed * DeltaTime));
	PendingKick -= Step;
	Recoverable += Step * RecoveryFraction;

	if (TimeSinceShot >= RecoveryDelay)
	{
		const FVector2D Back = Recoverable * (1.0 - FMath::Exp(-RecoverySpeed * DeltaTime));
		Recoverable -= Back;
		Step -= Back;
	}

	const float MinPitch = Player->PlayerCameraManager ? Player->PlayerCameraManager->ViewPitchMin : -89.0f;
	const float MaxPitch = Player->PlayerCameraManager ? Player->PlayerCameraManager->ViewPitchMax : 89.0f;
	Rotation.Pitch = FMath::Clamp(FRotator::NormalizeAxis(Rotation.Pitch) + Step.X, MinPitch, MaxPitch);
	Rotation.Yaw += Step.Y;
	Player->SetControlRotation(Rotation);

	LastControlRotation = Rotation;
	bHasLastControlRotation = true;

	// under a hundredth of a degree left: done
	if (PendingKick.SizeSquared() < 1.e-4 && Recoverable.SizeSquared() < 1.e-4)
	{
		Stop();
	}
}

void UKochRecoilComponent::Stop()
{
	PendingKick = FVector2D::ZeroVector;
	Recoverable = FVector2D::ZeroVector;
	bHasLastControlRotation = false;
	SetComponentTickEnabled(false);
}
