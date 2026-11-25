// See KochStanceComponent.h.

#include "Player/KochStanceComponent.h"
#include "Camera/CameraComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/LocalPlayer.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "InputAction.h"
#include "InputMappingContext.h"

UKochStanceComponent::UKochStanceComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = false;
}

void UKochStanceComponent::BeginPlay()
{
	Super::BeginPlay();

	Character = Cast<ACharacter>(GetOwner());
	if (!Character)
	{
		return;
	}

	Movement = Character->GetCharacterMovement();
	Camera = Character->FindComponentByClass<UCameraComponent>();
	if (Camera)
	{
		HipFieldOfView = Camera->FieldOfView;
		HipFirstPersonFieldOfView = Camera->FirstPersonFieldOfView;

		// the template camera sits on the first-person rig's head socket, so moving the rig moves the eye
		ViewRig = Camera->GetAttachParent();
	}
	if (ViewRig)
	{
		ViewRigRestLocation = ViewRig->GetRelativeLocation();
	}

	Movement->GetNavAgentPropertiesRef().bCanCrouch = true;
	Movement->SetCrouchedHalfHeight(CrouchedHalfHeight);
	Movement->MaxAcceleration = Acceleration;
	Movement->BrakingDecelerationWalking = BrakingDeceleration;

	UpdateState();
}

void UKochStanceComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	Super::EndPlay(EndPlayReason);

	// the context belongs to the local player, not to this pawn: take it back, or every respawn adds another
	if (UEnhancedInputLocalPlayerSubsystem* Subsystem = InputSubsystem.Get())
	{
		if (MappingContext)
		{
			Subsystem->RemoveMappingContext(MappingContext);
		}
	}
}

void UKochStanceComponent::SetupInput(UEnhancedInputComponent* Input)
{
	if (!Input)
	{
		return;
	}

	// no assets assigned: default actions and keys, so the stance works on any Blueprint child without setup
	const bool bDefaultActions = !AimAction || !SprintAction || !CrouchAction;
	if (!AimAction)
	{
		AimAction = NewObject<UInputAction>(this, TEXT("IA_KochAim"));
	}
	if (!SprintAction)
	{
		SprintAction = NewObject<UInputAction>(this, TEXT("IA_KochSprint"));
	}
	if (!CrouchAction)
	{
		CrouchAction = NewObject<UInputAction>(this, TEXT("IA_KochCrouch"));
	}
	if (!MappingContext || bDefaultActions)
	{
		MappingContext = NewObject<UInputMappingContext>(this, TEXT("IMC_KochStance"));
		MappingContext->MapKey(AimAction, EKeys::RightMouseButton);
		MappingContext->MapKey(AimAction, EKeys::Gamepad_LeftTrigger);
		MappingContext->MapKey(SprintAction, EKeys::LeftShift);
		MappingContext->MapKey(SprintAction, EKeys::Gamepad_LeftThumbstick);
		MappingContext->MapKey(CrouchAction, EKeys::LeftControl);
		MappingContext->MapKey(CrouchAction, EKeys::C);
		MappingContext->MapKey(CrouchAction, EKeys::Gamepad_RightThumbstick);
	}

	Input->BindAction(AimAction, ETriggerEvent::Started, this, &UKochStanceComponent::StartAim);
	Input->BindAction(AimAction, ETriggerEvent::Completed, this, &UKochStanceComponent::StopAim);
	Input->BindAction(SprintAction, ETriggerEvent::Started, this, &UKochStanceComponent::StartSprint);
	Input->BindAction(SprintAction, ETriggerEvent::Completed, this, &UKochStanceComponent::StopSprint);
	Input->BindAction(CrouchAction, ETriggerEvent::Started, this, &UKochStanceComponent::ToggleCrouch);

	const APawn* Pawn = Cast<APawn>(GetOwner());
	const APlayerController* Player = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
	const ULocalPlayer* LocalPlayer = Player ? Player->GetLocalPlayer() : nullptr;
	if (UEnhancedInputLocalPlayerSubsystem* Subsystem = LocalPlayer ? LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>() : nullptr)
	{
		Subsystem->AddMappingContext(MappingContext, MappingPriority);
		InputSubsystem = Subsystem;
	}
}

void UKochStanceComponent::StartAim()
{
	bWantsAim = true;
	UpdateState();
}

void UKochStanceComponent::StopAim()
{
	bWantsAim = false;
	UpdateState();
}

void UKochStanceComponent::StartSprint()
{
	bWantsSprint = true;

	// sprinting stands the player up
	if (Character && Movement && Movement->bWantsToCrouch)
	{
		Character->UnCrouch();
	}
	UpdateState();
}

void UKochStanceComponent::StopSprint()
{
	bWantsSprint = false;
	UpdateState();
}

void UKochStanceComponent::ToggleCrouch()
{
	if (!Character || !Movement)
	{
		return;
	}

	if (Movement->bWantsToCrouch)
	{
		Character->UnCrouch();
	}
	else
	{
		Character->Crouch();
	}
	UpdateState();
}

void UKochStanceComponent::SetWeaponReady(bool bReady)
{
	bWeaponReady = bReady;
	UpdateState();
}

void UKochStanceComponent::NotifyFired()
{
	SprintLock = SprintLockAfterShot;
	UpdateState();
}

float UKochStanceComponent::GetSpreadScale() const
{
	float Scale = FMath::Lerp(1.0f, AimSpreadScale, AimAlpha);
	if (Character && Movement)
	{
		if (Movement->IsFalling())
		{
			Scale *= AirborneSpreadScale;
		}
		else if (Character->GetVelocity().SizeSquared2D() > FMath::Square(MovingSpeedThreshold))
		{
			Scale *= MovingSpreadScale;
		}
		if (Character->bIsCrouched)
		{
			Scale *= CrouchSpreadScale;
		}
	}
	return Scale;
}

float UKochStanceComponent::GetLookScale() const
{
	// same on-screen speed at both fields of view: scale by the ratio of their half-angle tangents
	const float Zoomed = FMath::Tan(FMath::DegreesToRadians(AimFieldOfView * 0.5f)) / FMath::Tan(FMath::DegreesToRadians(HipFieldOfView * 0.5f));
	return FMath::Lerp(1.0f, Zoomed, AimAlpha);
}

bool UKochStanceComponent::CanSprint() const
{
	// forward only, judged by the input direction so a sprint can start from standing
	const FVector Push = Movement->GetCurrentAcceleration().GetSafeNormal2D();
	return SprintLock <= 0.0f
		&& Stamina > 0.0f
		&& !Movement->bWantsToCrouch
		&& Movement->IsMovingOnGround()
		&& FVector::DotProduct(Push, Character->GetActorForwardVector()) > 0.5f;
}

void UKochStanceComponent::UpdateState()
{
	if (!Character || !Movement)
	{
		return;
	}

	const bool bWasSprinting = bSprinting;

	// aiming wins over sprinting; a sprint needs some stamina to start but may run the bar down to empty
	bAiming = bWantsAim && bWeaponReady;
	bSprinting = bWantsSprint && !bAiming && CanSprint() && (bWasSprinting || Stamina >= MinStaminaToSprint);
	if (bWasSprinting && !bSprinting)
	{
		TimeSinceSprint = 0.0f;
	}

	const float AimScale = bAiming ? AimSpeedScale : 1.0f;
	Movement->MaxWalkSpeed = bSprinting ? SprintSpeed : JogSpeed * AimScale;
	Movement->MaxWalkSpeedCrouched = CrouchSpeed * AimScale;

	// the tick turns itself off again once everything has settled
	SetComponentTickEnabled(true);
}

void UKochStanceComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (!Character || !Movement)
	{
		SetComponentTickEnabled(false);
		return;
	}

	SprintLock = FMath::Max(0.0f, SprintLock - DeltaTime);

	// sprint conditions change without an input event: the player stops, leaves the ground or runs dry
	if (bWantsSprint || bSprinting)
	{
		UpdateState();
	}

	if (bSprinting)
	{
		Stamina = FMath::Max(0.0f, Stamina - DeltaTime / SprintSeconds);
	}
	else
	{
		TimeSinceSprint += DeltaTime;
		if (TimeSinceSprint >= StaminaRegenDelay)
		{
			Stamina = FMath::Min(1.0f, Stamina + DeltaTime / StaminaRegenSeconds);
		}
	}

	const float AimTarget = bAiming ? 1.0f : 0.0f;
	const float CrouchTarget = Character->bIsCrouched ? 1.0f : 0.0f;

	// bIsCrouched follows bWantsToCrouch a movement update later (or never, under a low ceiling)
	const bool bSettled = FMath::IsNearlyEqual(AimAlpha, AimTarget, 1.e-3f)
		&& FMath::IsNearlyEqual(CrouchAlpha, CrouchTarget, 1.e-3f)
		&& Movement->bWantsToCrouch == Character->bIsCrouched
		&& !bWantsSprint
		&& !bSprinting
		&& Stamina >= 1.0f
		&& SprintLock <= 0.0f;

	AimAlpha = bSettled ? AimTarget : FMath::FInterpTo(AimAlpha, AimTarget, DeltaTime, AimBlendSpeed);
	CrouchAlpha = bSettled ? CrouchTarget : FMath::FInterpTo(CrouchAlpha, CrouchTarget, DeltaTime, CrouchBlendSpeed);

	if (Camera)
	{
		Camera->SetFieldOfView(FMath::Lerp(HipFieldOfView, AimFieldOfView, AimAlpha));
		Camera->SetFirstPersonFieldOfView(FMath::Lerp(HipFirstPersonFieldOfView, AimFirstPersonFieldOfView, AimAlpha));
	}
	if (ViewRig)
	{
		ViewRig->SetRelativeLocation(ViewRigRestLocation - FVector(0.0, 0.0, CrouchEyeDrop * CrouchAlpha));
	}

	if (bSettled)
	{
		SetComponentTickEnabled(false);
	}
}
