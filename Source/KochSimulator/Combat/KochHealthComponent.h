// Health with per-zone damage (head / torso / arm / leg). Owner: any actor that can be shot; AKochGuard forwards TakeDamage to HandleDamage.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Combat/KochCombatTypes.h"
#include "KochHealthComponent.generated.h"

class USkinnedMeshComponent;
struct FDamageEvent;

DECLARE_MULTICAST_DELEGATE_OneParam(FKochDamageDelegate, const FKochDamageInfo&);

UCLASS(ClassGroup=(Koch), meta=(BlueprintSpawnableComponent))
class KOCHSIMULATOR_API UKochHealthComponent : public UActorComponent
{
	GENERATED_BODY()

public:

	UKochHealthComponent();

	/**
	 * Call from the owner's TakeDamage. Point damage (bullets) is scaled by the zone of the bone that was hit.
	 * @return damage applied after scaling; 0 once dead
	 */
	float HandleDamage(float Damage, const FDamageEvent& DamageEvent, AController* EventInstigator);

	/** Zone of a bone: the nearest ancestor (or the bone itself) listed in BoneZones. */
	EKochHitZone FindZone(const USkinnedMeshComponent* Mesh, FName BoneName) const;

	UFUNCTION(BlueprintPure, Category="Health")
	float GetHealth() const { return Health; }

	UFUNCTION(BlueprintPure, Category="Health")
	float GetMaxHealth() const { return MaxHealth; }

	UFUNCTION(BlueprintPure, Category="Health")
	bool IsDead() const { return bDead; }

	/** Every hit that did damage, the killing one included (bKilled set). */
	FKochDamageDelegate OnDamaged;

protected:

	virtual void BeginPlay() override;

	UPROPERTY(EditAnywhere, Category="Health", meta=(ClampMin=1))
	float MaxHealth = 100.0f;

	/** Damage scale per zone. With a 55-damage rifle round: head kills at once, two torso hits kill, limbs take four. */
	UPROPERTY(EditAnywhere, Category="Health")
	TMap<EKochHitZone, float> ZoneDamageMultipliers;

	/** Key bones only; children inherit (hand -> upperarm_l -> Arm). Defaults fit the UE5 mannequin and MetaHuman body skeletons. */
	UPROPERTY(EditAnywhere, Category="Health")
	TMap<FName, EKochHitZone> BoneZones;

private:

	float Health = 0.0f;

	bool bDead = false;
};
