// See KochViewMotionComponent.h.

#include "Player/KochViewMotionComponent.h"
#include "Player/KochStanceComponent.h"
#include "Camera/CameraComponent.h"
#include "Components/SceneComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "ShooterWeapon.h"

UKochViewMotionComponent::UKochViewMotionComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = false;
}

void UKochViewMotionComponent::BeginPlay()
{
	Super::BeginPlay();

	Character = Cast<ACharacter>(GetOwner());
	if (!Character)
	{
		return;
	}

	Camera = Character->FindComponentByClass<UCameraComponent>();
	Stance = Character->FindComponentByClass<UKochStanceComponent>();
	if (Camera)
	{
		RestLocation = Camera->GetRelativeLocation();

		// the sight and head sockets must be this frame's, or the aligned sight trembles while moving
		if (USceneComponent* Rig = Camera->GetAttachParent())
		{
			AddTickPrerequisiteComponent(Rig);
		}
	}

	Character->LandedDelegate.AddDynamic(this, &UKochViewMotionComponent::OnLanded);
}

void UKochViewMotionComponent::SetWeapon(AShooterWeapon* Weapon)
{
	CurrentWeapon = Weapon;
	bHasLastViewRotation = false;

	// with no weapon the tick runs on until everything is back at rest
	SetComponentTickEnabled(true);
}

void UKochViewMotionComponent::NotifyFired()
{
	// a jump, not a ramp: the jolt of a shot is instant; the spring only brings it back
	Impulse.X = FMath::Min(Impulse.X + FireKick, FireKick * 2.0);
}

void UKochViewMotionComponent::OnLanded(const FHitResult& Hit)
{
	if (CurrentWeapon && Character)
	{
		const float FallSpeed = FMath::Abs(Character->GetVelocity().Z);
		Impulse.Y = LandingDip * FMath::Clamp(FallSpeed / LandingReferenceSpeed, 0.2f, 1.5f);
	}
}

void UKochViewMotionComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (!Character || !Camera)
	{
		SetComponentTickEnabled(false);
		return;
	}

	const bool bHasWeapon = CurrentWeapon != nullptr;
	WeaponAlpha = FMath::FInterpTo(WeaponAlpha, bHasWeapon ? 1.0f : 0.0f, DeltaTime, 8.0f);

	const float AimAlpha = Stance ? Stance->GetAimAlpha() : 0.0f;
	const float Loose = MotionScale * FMath::Lerp(1.0f, AimMotionScale, AimAlpha);

	// sway: the weapon is left behind by a turn and catches up on a spring
	const FRotator ViewRotation = Character->GetViewRotation();
	double SwayTargetYaw = 0.0;
	double SwayTargetPitch = 0.0;
	if (bHasLastViewRotation && DeltaTime > UE_SMALL_NUMBER)
	{
		const double YawRate = FRotator::NormalizeAxis(ViewRotation.Yaw - LastViewRotation.Yaw) / DeltaTime;
		const double PitchRate = FRotator::NormalizeAxis(ViewRotation.Pitch - LastViewRotation.Pitch) / DeltaTime;
		SwayTargetYaw = FMath::Clamp<double>(YawRate * SwayPerDegreePerSecond, -MaxSway, MaxSway);
		SwayTargetPitch = FMath::Clamp<double>(PitchRate * SwayPerDegreePerSecond, -MaxSway, MaxSway);
	}
	LastViewRotation = ViewRotation;
	bHasLastViewRotation = true;
	FMath::SpringDamper(Sway.X, SwayRate.X, SwayTargetYaw, 0.0, DeltaTime, SwayFrequency, SwayDamping);
	FMath::SpringDamper(Sway.Y, SwayRate.Y, SwayTargetPitch, 0.0, DeltaTime, SwayFrequency, SwayDamping);

	// bob: one side-to-side swing per two steps, two up-down bounces in the same distance
	const UCharacterMovementComponent* Movement = Character->GetCharacterMovement();
	const float Speed = Character->GetVelocity().Size2D();
	const bool bOnFoot = Movement && Movement->IsMovingOnGround();
	BobAmount = FMath::FInterpTo(BobAmount, bOnFoot ? FMath::Min(Speed / JogReferenceSpeed, MaxBobScale) : 0.0f, DeltaTime, 6.0f);
	if (bOnFoot)
	{
		BobPhase = FMath::Fmod(BobPhase + Speed / StrideLength * UE_TWO_PI * DeltaTime, UE_TWO_PI);
	}
	const float BobSideNow = FMath::Sin(BobPhase) * BobSide * BobAmount;
	const float BobUpNow = FMath::Sin(BobPhase * 2.0f) * BobUp * BobAmount;

	// breathing is not reduced while aiming: it is what keeps a held aim from looking frozen
	BreathPhase = FMath::Fmod(BreathPhase + BreathFrequency * UE_TWO_PI * DeltaTime, UE_TWO_PI);
	const float Breath = FMath::Sin(BreathPhase) * BreathAmplitude * MotionScale;

	// shot jolt (X) and landing dip (Y) return to zero, critically damped
	FMath::SpringDamper(Impulse.X, ImpulseRate.X, 0.0, 0.0, DeltaTime, ImpulseFrequency, 1.0f);
	FMath::SpringDamper(Impulse.Y, ImpulseRate.Y, 0.0, 0.0, DeltaTime, ImpulseFrequency, 1.0f);

	// where the weapon should appear to go, view space: X away from the eye, Y right, Z up
	const FVector WeaponOffset(
		-Impulse.X,
		(BobSideNow - Sway.X) * Loose,
		(BobUpNow - Sway.Y - Impulse.Y) * Loose + Breath);

	// the camera goes the other way
	FVector CameraOffset = -WeaponOffset * WeaponAlpha;

	const USceneComponent* Rig = Camera->GetAttachParent();
	const FTransform RigSocket = Rig ? Rig->GetSocketTransform(Camera->GetAttachSocketName()) : Character->GetActorTransform();
	const FVector RestWorld = RigSocket.TransformPosition(RestLocation);
	const FQuat ViewQuat = ViewRotation.Quaternion();

	// aiming: put the eye on the sight line by cancelling the sight's offset from the view axis
	if (bHasWeapon && AimAlpha > 0.0f)
	{
		const FVector Sight = ViewQuat.UnrotateVector(CurrentWeapon->GetSightLocation() - RestWorld);
		const FVector Align(AimEyeRelief > 0.0f ? Sight.X - AimEyeRelief : 0.0, Sight.Y, Sight.Z);
		CameraOffset += Align * (AimAlpha * WeaponAlpha);
	}

	Camera->SetRelativeLocation(RigSocket.InverseTransformPosition(RestWorld + ViewQuat.RotateVector(CameraOffset)));

	// nothing in hand and everything settled: back to the exact rest pose, stop ticking
	if (!bHasWeapon && WeaponAlpha < 1.e-3f)
	{
		WeaponAlpha = 0.0f;
		Sway = SwayRate = Impulse = ImpulseRate = FVector2D::ZeroVector;
		Camera->SetRelativeLocation(RestLocation);
		SetComponentTickEnabled(false);
	}
}
