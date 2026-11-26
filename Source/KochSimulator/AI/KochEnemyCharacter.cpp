// See KochEnemyCharacter.h.

#include "KochEnemyCharacter.h"
#include "KochDifficultySubsystem.h"
#include "KochSquadSubsystem.h"
#include "KochAwarenessComponent.h"
#include "KochKillFeedSubsystem.h"
#include "AIController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "ShooterWeapon.h"
#include "Engine/World.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Components/CapsuleComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "TimerManager.h"

namespace
{
	constexpr float FootstepTickInterval = 0.05f; // s; at most 50 ms late at ~3 steps/s
}

AKochEnemyCharacter::AKochEnemyCharacter()
{
	Awareness = CreateDefaultSubobject<UKochAwarenessComponent>(TEXT("Awareness"));

	// MetaHuman parts on the third-person body; empty by default (plain Manny enemies leave them unset).
	FaceMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("FaceMesh"));
	FaceMesh->SetupAttachment(GetMesh());
	FaceMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	OutfitMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("OutfitMesh"));
	OutfitMesh->SetupAttachment(GetMesh());
	OutfitMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	// Generic defaults from docs/design/enemies.md §3a/§5 (Medium = struct defaults for awareness); BP children override per type.
	FKochEnemyTuning Easy;
	Easy.ReactionTime = 0.6f;
	Easy.AimConeStill = 6.0f;
	Easy.AimConeRunning = 15.0f;
	Easy.RunSpeed = 340.0f;
	Easy.MaxHealth = 80.0f;
	Easy.SightRange = 2500.0f;
	Easy.SightHalfAngle = 55.0f;
	Easy.NoticeTime = 0.9f;
	Easy.HearingRange = 2000.0f;
	Easy.MemoryTime = 5.0f;
	Easy.SearchTime = 6.0f;

	FKochEnemyTuning Medium;
	Medium.ReactionTime = 0.35f;
	Medium.AimConeStill = 3.5f;
	Medium.AimConeRunning = 12.0f;
	Medium.RunSpeed = 400.0f;
	Medium.MaxHealth = 100.0f;

	FKochEnemyTuning Hard;
	Hard.ReactionTime = 0.2f;
	Hard.AimConeStill = 2.0f;
	Hard.AimConeRunning = 10.0f;
	Hard.RunSpeed = 440.0f;
	Hard.MaxHealth = 125.0f;
	Hard.SightRange = 4500.0f;
	Hard.SightHalfAngle = 80.0f;
	Hard.NoticeTime = 0.25f;
	Hard.HearingRange = 4000.0f;
	Hard.MemoryTime = 12.0f;
	Hard.SearchTime = 20.0f;

	Tuning.Add(EKochDifficulty::Easy, Easy);
	Tuning.Add(EKochDifficulty::Medium, Medium);
	Tuning.Add(EKochDifficulty::Hard, Hard);
}

void AKochEnemyCharacter::BeginPlay()
{
	if (!FMath::IsNearlyEqual(BodyScale, 1.0f))
	{
		SetActorScale3D(FVector(BodyScale));
	}
	AnchorLocation = GetActorLocation();

	// Face, outfit and any clothing piece the BP attaches to the body (top, pants, shoes) copy the body's
	// animated pose: no own anim instance, cheap for NPCs. Parts with their own anim class are left alone.
	TInlineComponentArray<USkeletalMeshComponent*> Parts(this);
	for (USkeletalMeshComponent* Part : Parts)
	{
		if (Part != GetMesh() && Part->GetAttachParent() == GetMesh() && Part->GetSkeletalMeshAsset() && !Part->GetAnimClass())
		{
			Part->SetLeaderPoseComponent(GetMesh());
		}
	}

	Super::BeginPlay();

	if (!bTuningApplied)
	{
		ApplyTuning(UKochDifficultySubsystem::GetCurrent(this));
	}
	if (UKochDifficultySubsystem* DifficultySubsystem = UKochDifficultySubsystem::Get(this))
	{
		DifficultySubsystem->OnDifficultyChanged.AddUniqueDynamic(this, &AKochEnemyCharacter::HandleDifficultyChanged);
	}
	if (UKochSquadSubsystem* Squad = GetWorld()->GetSubsystem<UKochSquadSubsystem>())
	{
		Squad->RegisterEnemy(this);
	}
	if (!FootstepSounds.IsEmpty())
	{
		GetWorldTimerManager().SetTimer(FootstepTimer, this, &AKochEnemyCharacter::UpdateFootsteps, FootstepTickInterval, true);
	}
}

void AKochEnemyCharacter::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UKochDifficultySubsystem* DifficultySubsystem = UKochDifficultySubsystem::Get(this))
	{
		DifficultySubsystem->OnDifficultyChanged.RemoveDynamic(this, &AKochEnemyCharacter::HandleDifficultyChanged);
	}
	if (UWorld* World = GetWorld())
	{
		if (UKochSquadSubsystem* Squad = World->GetSubsystem<UKochSquadSubsystem>())
		{
			Squad->UnregisterEnemy(this);
		}
	}
	GetWorldTimerManager().ClearTimer(FootstepTimer);
	Super::EndPlay(EndPlayReason);
}

void AKochEnemyCharacter::PossessedBy(AController* NewController)
{
	Super::PossessedBy(NewController);
	if (!bTuningApplied)
	{
		ApplyTuning(UKochDifficultySubsystem::GetCurrent(this)); // possession can precede BeginPlay
	}
	Awareness->BindToController(Cast<AAIController>(NewController));
}

void AKochEnemyCharacter::UnPossessed()
{
	Awareness->Unbind();
	Super::UnPossessed();
}

void AKochEnemyCharacter::HandleDifficultyChanged(EKochDifficulty NewDifficulty)
{
	ApplyTuning(NewDifficulty);
	Awareness->ApplyPerceptionTuning();
}

void AKochEnemyCharacter::ApplyTuning(EKochDifficulty Difficulty)
{
	const float OldMaxHealth = ActiveTuning.MaxHealth;
	const FKochEnemyTuning* Found = Tuning.Find(Difficulty);
	ActiveTuning = Found ? *Found : FKochEnemyTuning();

	// Full HP on the first apply (spawn); keep the HP fraction when difficulty changes mid-fight.
	if (!bIsDead)
	{
		CurrentHP = bTuningApplied ? CurrentHP / FMath::Max(OldMaxHealth, 1.0f) * ActiveTuning.MaxHealth : ActiveTuning.MaxHealth;
	}
	bTuningApplied = true;

	if (UCharacterMovementComponent* Move = GetCharacterMovement())
	{
		Move->MaxWalkSpeedCrouched = ActiveTuning.CrouchSpeed;
		Move->MaxAcceleration = ActiveTuning.MaxAcceleration;
		Move->BrakingDecelerationWalking = ActiveTuning.BrakingDeceleration;
		// Braking driven only by BrakingDecelerationWalking, so stop times are predictable (CS counter-strafe).
		Move->bUseSeparateBrakingFriction = true;
		Move->BrakingFriction = 0.0f;
		Move->GetNavAgentPropertiesRef().bCanCrouch = true;
	}
	ApplyMoveSpeed();
}

void AKochEnemyCharacter::SetElroy(bool bNewElroy)
{
	if (bElroy != bNewElroy)
	{
		bElroy = bNewElroy;
		ApplyMoveSpeed();
	}
}

void AKochEnemyCharacter::SetMoveSpeedScale(float Scale)
{
	MoveSpeedScale = FMath::Clamp(Scale, 0.1f, 1.0f);
	ApplyMoveSpeed();
}

void AKochEnemyCharacter::ApplyMoveSpeed()
{
	if (UCharacterMovementComponent* Move = GetCharacterMovement())
	{
		Move->MaxWalkSpeed = ActiveTuning.RunSpeed * MoveSpeedScale * (bElroy ? 1.0f + ElroySpeedBonus : 1.0f);
	}
}

FVector AKochEnemyCharacter::GetWeaponTargetLocation()
{
	const float Speed2D = GetVelocity().Size2D();
	const float SpeedRatio = Speed2D / FMath::Max(ActiveTuning.RunSpeed, 1.0f);

	float Cone = ActiveTuning.AimConeStill;
	if (SpeedRatio > ActiveTuning.AccurateSpeedRatio)
	{
		Cone = FMath::GetMappedRangeValueClamped(
			FVector2f(ActiveTuning.AccurateSpeedRatio, 1.0f),
			FVector2f(ActiveTuning.AimConeStill, ActiveTuning.AimConeRunning),
			SpeedRatio);
	}
	if (bIsCrouched)
	{
		Cone *= ActiveTuning.CrouchConeScale;
	}

	AimVarianceHalfAngle = Cone; // consumed by AShooterNPC's cone sampling
	return Super::GetWeaponTargetLocation();
}

void AKochEnemyCharacter::AttachWeaponMeshes(AShooterWeapon* WeaponToAttach)
{
	Super::AttachWeaponMeshes(WeaponToAttach);

	USkeletalMeshComponent* Body = GetMesh();
	USkeletalMeshComponent* WeaponMesh = WeaponToAttach ? WeaponToAttach->GetThirdPersonMesh() : nullptr;
	if (!Body || !WeaponMesh)
	{
		return;
	}
	if (!Body->DoesSocketExist(ThirdPersonWeaponSocket) && Body->DoesSocketExist(WeaponFallbackBone))
	{
		WeaponMesh->AttachToComponent(Body, FAttachmentTransformRules(EAttachmentRule::SnapToTarget, false), WeaponFallbackBone);
		WeaponMesh->SetRelativeTransform(WeaponFallbackOffset);
	}
	// A small enemy still carries a full-size rifle.
	WeaponMesh->SetWorldScale3D(FVector::OneVector);

	// Nobody sees an NPC's first-person rifle, but projectiles spawn at its muzzle: keep it on the visible one.
	if (USkeletalMeshComponent* FirstPersonWeapon = WeaponToAttach->GetFirstPersonMesh())
	{
		FirstPersonWeapon->AttachToComponent(WeaponMesh, FAttachmentTransformRules::SnapToTargetIncludingScale);
		FirstPersonWeapon->SetVisibility(false);
	}
}

void AKochEnemyCharacter::PlayFiringMontage(UAnimMontage* Montage)
{
	// The weapon passes its own first-person montages; the body plays this enemy's third-person ones instead.
	UAnimInstance* AnimInstance = GetMesh() ? GetMesh()->GetAnimInstance() : nullptr;
	if (!AnimInstance || bIsDead)
	{
		return;
	}
	UAnimMontage* BodyMontage = (Weapon && Weapon->IsReloading()) ? ReloadMontage.Get() : FireMontage.Get();
	if (BodyMontage)
	{
		AnimInstance->Montage_Play(BodyMontage);
	}
}

float AKochEnemyCharacter::TakeDamage(float Damage, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
	const bool bWasDead = bIsDead;
	const float Applied = Super::TakeDamage(Damage, DamageEvent, EventInstigator, DamageCauser);
	if (bIsDead && !bWasDead)
	{
		UKochKillFeedSubsystem::ReportDeath(this, DamageEvent, EventInstigator, DamageCauser);
	}
	if (bIsDead || Applied <= 0.0f)
	{
		return Applied;
	}

	// Flinch away from the shooter (the projectile may already be past us, so prefer the instigator).
	const AActor* Source = EventInstigator && EventInstigator->GetPawn() ? EventInstigator->GetPawn() : DamageCauser;
	UAnimInstance* AnimInstance = GetMesh() ? GetMesh()->GetAnimInstance() : nullptr;
	if (!Source || !AnimInstance)
	{
		return Applied;
	}
	const FVector LocalDir = GetActorRotation().UnrotateVector(Source->GetActorLocation() - GetActorLocation());
	const float Angle = FMath::RadiansToDegrees(FMath::Atan2(LocalDir.Y, LocalDir.X)); // 0 = front, +90 = right
	UAnimMontage* HitReact = FMath::Abs(Angle) <= 45.0f ? HitReactFront.Get()
		: FMath::Abs(Angle) >= 135.0f ? HitReactBack.Get()
		: Angle > 0.0f ? HitReactRight.Get() : HitReactLeft.Get();
	if (HitReact)
	{
		AnimInstance->Montage_Play(HitReact);
	}
	return Applied;
}

void AKochEnemyCharacter::UpdateFootsteps()
{
	const UCharacterMovementComponent* Move = GetCharacterMovement();
	const float Speed = GetVelocity().Size2D();
	if (bIsDead || bIsCrouched || !Move || !Move->IsMovingOnGround() || Speed < FootstepSpeedRatio * ActiveTuning.RunSpeed)
	{
		FootstepDistance = 0.0f;
		return;
	}

	FootstepDistance += Speed * FootstepTickInterval;
	const float Stride = FootstepStride * BodyScale;
	if (FootstepDistance < Stride)
	{
		return;
	}
	FootstepDistance = FMath::Fmod(FootstepDistance, Stride);
	if (USoundBase* Sound = FootstepSounds[FMath::RandHelper(FootstepSounds.Num())])
	{
		const FVector Feet = GetActorLocation() - FVector(0.0f, 0.0f, GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
		UGameplayStatics::PlaySoundAtLocation(this, Sound, Feet);
	}
}
