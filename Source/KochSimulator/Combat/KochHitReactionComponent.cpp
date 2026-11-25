// See KochHitReactionComponent.h.

#include "Combat/KochHitReactionComponent.h"
#include "Combat/KochImpactEffects.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimSequenceBase.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "TimerManager.h"

UKochHitReactionComponent::UKochHitReactionComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = false;

	// world-space targets: the simulated bodies chase the animated pose. Strengths from Epic's physical animation docs.
	FlinchDrive.bIsLocalSimulation = false;
	FlinchDrive.OrientationStrength = 1000.0f;
	FlinchDrive.AngularVelocityStrength = 100.0f;
	FlinchDrive.PositionStrength = 1000.0f;
	FlinchDrive.VelocityStrength = 100.0f;

	// weaker than the flinch: the shot has to be able to move the body
	DeathDrive.bIsLocalSimulation = false;
	DeathDrive.OrientationStrength = 400.0f;
	DeathDrive.AngularVelocityStrength = 40.0f;
	DeathDrive.PositionStrength = 400.0f;
	DeathDrive.VelocityStrength = 40.0f;
}

void UKochHitReactionComponent::BeginPlay()
{
	Super::BeginPlay();

	const ACharacter* Character = Cast<ACharacter>(GetOwner());
	Mesh = Character ? Character->GetMesh() : GetOwner()->FindComponentByClass<USkeletalMeshComponent>();
	if (!Mesh)
	{
		return;
	}

	// bullets must reach the physics-asset bodies (hit zones), so the capsule lets them through
	if (Character)
	{
		Character->GetCapsuleComponent()->SetCollisionResponseToChannel(Koch::BulletChannel, ECR_Ignore);
	}

	// simulating bodies need physics collision (CharacterMesh is query-only). Pawns stay ignored, and loose physics bodies too,
	// so a living character never kicks corpses, cases or dropped guns around.
	Mesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	Mesh->SetCollisionResponseToChannel(Koch::BulletChannel, ECR_Block);
	Mesh->SetCollisionResponseToChannel(ECC_PhysicsBody, ECR_Ignore);

	PhysicalAnimation = NewObject<UPhysicalAnimationComponent>(GetOwner(), TEXT("KochPhysicalAnimation"));
	PhysicalAnimation->RegisterComponent();
	PhysicalAnimation->SetSkeletalMeshComponent(Mesh);
}

void UKochHitReactionComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	Super::EndPlay(EndPlayReason);

	GetWorld()->GetTimerManager().ClearTimer(BloodPoolTimer);
}

void UKochHitReactionComponent::PlayHitReaction(const FKochDamageInfo& Info)
{
	if (!Mesh || State >= EState::Dying)
	{
		return;
	}

	PlayDirectionalAnim(HitAnimsFront, HitAnimsBack, Info.ShotDirection, 0.2f);

	if (Info.Zone == EKochHitZone::Leg || Info.ShotDirection.IsZero())
	{
		return;
	}

	if (State == EState::Idle)
	{
		PhysicalAnimation->ApplyPhysicalAnimationSettingsBelow(FlinchRootBone, FlinchDrive, true);
		PhysicalAnimation->SetStrengthMultiplyer(1.0f);
		Mesh->SetAllBodiesBelowSimulatePhysics(FlinchRootBone, true, true);
	}
	Mesh->SetAllBodiesBelowPhysicsBlendWeight(FlinchRootBone, 1.0f, false, true);

	// a hit below the simulated chain (pelvis, spine_01) still rocks the upper body
	const FName ImpulseBone = Mesh->IsSimulatingPhysics(Info.BoneName) ? Info.BoneName : FlinchRootBone;
	Mesh->AddImpulseAtLocation(Info.ShotDirection * (Info.Damage * FlinchImpulsePerDamage), Info.HitLocation, ImpulseBone);

	State = EState::FlinchHold;
	StateTime = 0.0f;
	SetComponentTickEnabled(true);
}

void UKochHitReactionComponent::StartDeath(const FKochDamageInfo& Info)
{
	if (!Mesh || State >= EState::Dying)
	{
		return;
	}

	State = EState::Dying;
	StateTime = 0.0f;
	LimpTime = Info.Zone == EKochHitZone::Head ? HeadshotLimpTime : DeathLimpTime;

	// the death animation is only the motor target; nothing blends out of it
	PlayDirectionalAnim(DeathAnimsFront, DeathAnimsBack, Info.ShotDirection, 0.0f);

	Mesh->SetCollisionProfileName(RagdollCollisionProfile);
	PhysicalAnimation->ApplyPhysicalAnimationSettingsBelow(RagdollRootBone, DeathDrive, true);
	PhysicalAnimation->SetStrengthMultiplyer(1.0f);
	Mesh->SetSimulatePhysics(true);
	Mesh->SetPhysicsBlendWeight(1.0f);

	if (!Info.ShotDirection.IsZero())
	{
		Mesh->AddImpulseAtLocation(Info.ShotDirection * (Info.Damage * DeathImpulsePerDamage), Info.HitLocation, Info.BoneName);
	}

	SetComponentTickEnabled(true);

	UWorld* World = GetWorld();
	if (BloodEffects)
	{
		World->GetTimerManager().SetTimer(BloodPoolTimer, this, &UKochHitReactionComponent::SpawnBloodPool, BloodPoolDelay, false);
	}
	if (UKochCorpseSubsystem* Corpses = World->GetSubsystem<UKochCorpseSubsystem>())
	{
		Corpses->AddCorpse(GetOwner());
	}
}

void UKochHitReactionComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	StateTime += DeltaTime;

	switch (State)
	{
	case EState::FlinchHold:
		if (StateTime >= FlinchHoldTime)
		{
			State = EState::FlinchRecover;
			StateTime = 0.0f;
		}
		break;

	case EState::FlinchRecover:
	{
		const float Alpha = FMath::Clamp(StateTime / FlinchRecoverTime, 0.0f, 1.0f);
		Mesh->SetAllBodiesBelowPhysicsBlendWeight(FlinchRootBone, 1.0f - Alpha, false, true);
		if (Alpha >= 1.0f)
		{
			Mesh->SetAllBodiesBelowSimulatePhysics(FlinchRootBone, false, true);
			State = EState::Idle;
			SetComponentTickEnabled(false);
		}
		break;
	}

	case EState::Dying:
	{
		const float Alpha = FMath::Clamp(StateTime / LimpTime, 0.0f, 1.0f);
		PhysicalAnimation->SetStrengthMultiplyer(1.0f - Alpha);
		if (Alpha >= 1.0f)
		{
			// plain ragdoll from here: the animation graph has nothing left to add
			Mesh->bPauseAnims = true;
			State = EState::Dead;
			SetComponentTickEnabled(false);
		}
		break;
	}

	default:
		SetComponentTickEnabled(false);
		break;
	}
}

void UKochHitReactionComponent::PlayDirectionalAnim(const TArray<TObjectPtr<UAnimSequenceBase>>& Front, const TArray<TObjectPtr<UAnimSequenceBase>>& Back, const FVector& ShotDirection, float BlendOutTime) const
{
	UAnimInstance* AnimInstance = Mesh->GetAnimInstance();
	if (!AnimInstance)
	{
		return;
	}

	// a shot travelling the way the character faces came from behind
	const bool bFromBehind = FVector::DotProduct(ShotDirection, GetOwner()->GetActorForwardVector()) > 0.0f;
	const TArray<TObjectPtr<UAnimSequenceBase>>& Pool = (bFromBehind && Back.Num() > 0) ? Back : Front;
	if (Pool.Num() == 0)
	{
		return;
	}

	if (UAnimSequenceBase* Sequence = Pool[FMath::RandHelper(Pool.Num())])
	{
		AnimInstance->PlaySlotAnimationAsDynamicMontage(Sequence, HitAnimSlot, 0.08f, BlendOutTime);
	}
}

void UKochHitReactionComponent::SpawnBloodPool()
{
	if (!Mesh || !BloodEffects)
	{
		return;
	}

	if (UKochImpactSubsystem* Impacts = GetWorld()->GetSubsystem<UKochImpactSubsystem>())
	{
		Impacts->SpawnBloodPool(*BloodEffects, Mesh->GetSocketLocation(RagdollRootBone), GetOwner());
	}
}

void UKochCorpseSubsystem::AddCorpse(AActor* Corpse)
{
	Corpses.RemoveAll([](const TWeakObjectPtr<AActor>& Entry) { return !Entry.IsValid(); });
	Corpses.Add(Corpse);

	while (Corpses.Num() > MaxCorpses)
	{
		if (AActor* Oldest = Corpses[0].Get())
		{
			Oldest->Destroy();
		}
		Corpses.RemoveAt(0, EAllowShrinking::No);
	}
}
