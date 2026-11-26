// See KochEnemyCharacter.h.

#include "KochEnemyCharacter.h"
#include "KochDifficultySubsystem.h"
#include "KochSquadSubsystem.h"
#include "KochAwarenessComponent.h"
#include "AIController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "ShooterWeapon.h"
#include "Engine/World.h"

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

	// Face and outfit copy the body's animated pose (no own anim instance: cheap for NPCs).
	for (USkeletalMeshComponent* Part : { FaceMesh.Get(), OutfitMesh.Get() })
	{
		if (Part && Part->GetSkeletalMeshAsset())
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
}
