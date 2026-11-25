// See KochGuard.h.

#include "AI/KochGuard.h"
#include "Combat/KochHealthComponent.h"
#include "Combat/KochHitReactionComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "ShooterWeapon.h"

AKochGuard::AKochGuard()
{
	Health = CreateDefaultSubobject<UKochHealthComponent>(TEXT("Health"));
	HitReaction = CreateDefaultSubobject<UKochHitReactionComponent>(TEXT("Hit Reaction"));

	// the body stays; UKochCorpseSubsystem caps how many
	DeferredDestructionTime = 0.0f;
}

void AKochGuard::BeginPlay()
{
	Super::BeginPlay();

	Health->OnDamaged.AddUObject(this, &AKochGuard::OnDamaged);
}

float AKochGuard::TakeDamage(float Damage, struct FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
	if (bIsDead)
	{
		return 0.0f;
	}

	return Health->HandleDamage(Damage, DamageEvent, EventInstigator);
}

void AKochGuard::OnDamaged(const FKochDamageInfo& Info)
{
	if (Info.bKilled)
	{
		KillingHit = Info;
		Die();
	}
	else
	{
		HitReaction->PlayHitReaction(Info);
	}
}

void AKochGuard::StartDeathPhysics()
{
	if (Weapon)
	{
		StopShooting();

		// the rifle falls out of the dead hand
		USkeletalMeshComponent* Gun = Weapon->GetThirdPersonMesh();
		Gun->DetachFromComponent(FDetachmentTransformRules::KeepWorldTransform);
		Gun->SetCollisionProfileName(FName("PhysicsActor"));
		Gun->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
		Gun->SetSimulatePhysics(true);
	}

	HitReaction->StartDeath(KillingHit);
}
