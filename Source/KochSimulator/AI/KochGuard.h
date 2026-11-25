// KOCH security guard: the template's shooter NPC with zoned health, physical hit reactions and a corpse that stays.
// Blueprint child: Content/KochSimulator/AI/BP_KochGuard. AI still runs on the template's StateTree (cover and tactics come later).

#pragma once

#include "CoreMinimal.h"
#include "Variant_Shooter/AI/ShooterNPC.h"
#include "Combat/KochCombatTypes.h"
#include "KochGuard.generated.h"

class UKochHealthComponent;
class UKochHitReactionComponent;

UCLASS(abstract)
class KOCHSIMULATOR_API AKochGuard : public AShooterNPC
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta=(AllowPrivateAccess="true"))
	TObjectPtr<UKochHealthComponent> Health;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta=(AllowPrivateAccess="true"))
	TObjectPtr<UKochHitReactionComponent> HitReaction;

public:

	AKochGuard();

	/** Routes damage through the health component (zones) instead of the template's flat HP. */
	virtual float TakeDamage(float Damage, struct FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser) override;

protected:

	virtual void BeginPlay() override;

	/** Drops the weapon and starts the powered ragdoll. */
	virtual void StartDeathPhysics() override;

private:

	void OnDamaged(const FKochDamageInfo& Info);

	/** Hit that killed the guard; drives the death impulse. */
	FKochDamageInfo KillingHit;
};
