// Physical hit reactions and death for a character: flinch where the bullet lands, then a powered ragdoll that goes limp.
// Owner: AKochGuard (any ACharacter with a physics asset works). Also holds UKochCorpseSubsystem, which caps bodies left in the world.
// Method: Epic's physics-based hit reaction recipe (simulate bodies below a bone, blend back) plus UPhysicalAnimationComponent
// motors faded to zero on death. Physics Control (5.8, production) is the planned upgrade; it needs a .uproject change.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "PhysicsEngine/PhysicalAnimationComponent.h"
#include "Subsystems/WorldSubsystem.h"
#include "Combat/KochCombatTypes.h"
#include "KochHitReactionComponent.generated.h"

class UAnimSequenceBase;
class UKochImpactEffectSet;
class USkeletalMeshComponent;

UCLASS(ClassGroup=(Koch), meta=(BlueprintSpawnableComponent))
class KOCHSIMULATOR_API UKochHitReactionComponent : public UActorComponent
{
	GENERATED_BODY()

public:

	UKochHitReactionComponent();

	/** Non-lethal hit: a hit-react animation plus a physical shove of the upper body. */
	void PlayHitReaction(const FKochDamageInfo& Info);

	/** Lethal hit: the whole body simulates, pushed by the shot; its muscles fade over DeathLimpTime (at once for a headshot). */
	void StartDeath(const FKochDamageInfo& Info);

	/** Ticks only while a flinch or a death is playing out. */
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

protected:

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	/** Bodies from this bone down simulate during a flinch. Legs stay animated: simulated legs under a moving capsule look broken. */
	UPROPERTY(EditAnywhere, Category="Flinch")
	FName FlinchRootBone = FName("spine_02");

	/** Impulse per point of damage (kg*cm/s). */
	UPROPERTY(EditAnywhere, Category="Flinch", meta=(ClampMin=0))
	float FlinchImpulsePerDamage = 45.0f;

	/** Seconds fully physical before blending back. */
	UPROPERTY(EditAnywhere, Category="Flinch", meta=(ClampMin=0, Units="s"))
	float FlinchHoldTime = 0.12f;

	/** Seconds to blend back to animation. */
	UPROPERTY(EditAnywhere, Category="Flinch", meta=(ClampMin=0.01, Units="s"))
	float FlinchRecoverTime = 0.35f;

	/** Motors pulling the simulated upper body back to its animated pose. */
	UPROPERTY(EditAnywhere, Category="Flinch")
	FPhysicalAnimationData FlinchDrive;

	/** Played in HitAnimSlot, one at random. Back is used for shots from behind (falls back to Front). */
	UPROPERTY(EditAnywhere, Category="Animation")
	TArray<TObjectPtr<UAnimSequenceBase>> HitAnimsFront;

	UPROPERTY(EditAnywhere, Category="Animation")
	TArray<TObjectPtr<UAnimSequenceBase>> HitAnimsBack;

	/** Death animation the dying body is pulled toward while its motors fade. Same front/back rule. */
	UPROPERTY(EditAnywhere, Category="Animation")
	TArray<TObjectPtr<UAnimSequenceBase>> DeathAnimsFront;

	UPROPERTY(EditAnywhere, Category="Animation")
	TArray<TObjectPtr<UAnimSequenceBase>> DeathAnimsBack;

	/** The Anim Blueprint needs a Slot node with this name for the animations above to show. */
	UPROPERTY(EditAnywhere, Category="Animation")
	FName HitAnimSlot = FName("DefaultSlot");

	UPROPERTY(EditAnywhere, Category="Death")
	FName RagdollRootBone = FName("pelvis");

	UPROPERTY(EditAnywhere, Category="Death")
	FName RagdollCollisionProfile = FName("Ragdoll");

	/** Impulse per point of damage at the hit bone (kg*cm/s). */
	UPROPERTY(EditAnywhere, Category="Death", meta=(ClampMin=0))
	float DeathImpulsePerDamage = 60.0f;

	/** Seconds the body keeps muscle tone before it is a plain ragdoll. */
	UPROPERTY(EditAnywhere, Category="Death", meta=(ClampMin=0.01, Units="s"))
	float DeathLimpTime = 0.7f;

	/** Same, for a headshot: the body drops at once. */
	UPROPERTY(EditAnywhere, Category="Death", meta=(ClampMin=0.01, Units="s"))
	float HeadshotLimpTime = 0.06f;

	/** Motors at the moment of death; their strength fades to zero. */
	UPROPERTY(EditAnywhere, Category="Death")
	FPhysicalAnimationData DeathDrive;

	/** Blood pool under the corpse (none: no pool). */
	UPROPERTY(EditAnywhere, Category="Death")
	TObjectPtr<UKochImpactEffectSet> BloodEffects;

	/** Seconds after death before the pool starts, so the body has come to rest. */
	UPROPERTY(EditAnywhere, Category="Death", meta=(ClampMin=0, Units="s"))
	float BloodPoolDelay = 2.5f;

private:

	enum class EState : uint8
	{
		Idle,
		FlinchHold,
		FlinchRecover,
		Dying,
		Dead
	};

	/** Plays one of the sequences in the slot; Back when the shot came from behind and Back has entries. */
	void PlayDirectionalAnim(const TArray<TObjectPtr<UAnimSequenceBase>>& Front, const TArray<TObjectPtr<UAnimSequenceBase>>& Back, const FVector& ShotDirection, float BlendOutTime) const;

	void SpawnBloodPool();

	UPROPERTY(Transient)
	TObjectPtr<USkeletalMeshComponent> Mesh;

	UPROPERTY(Transient)
	TObjectPtr<UPhysicalAnimationComponent> PhysicalAnimation;

	EState State = EState::Idle;

	/** Seconds in the current state. */
	float StateTime = 0.0f;

	/** DeathLimpTime or HeadshotLimpTime for the death in progress. */
	float LimpTime = 0.0f;

	FTimerHandle BloodPoolTimer;
};

/** Caps corpses: past MaxCorpses the oldest is destroyed. Replaces the template's 5 s despawn. */
UCLASS()
class KOCHSIMULATOR_API UKochCorpseSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:

	void AddCorpse(AActor* Corpse);

private:

	TArray<TWeakObjectPtr<AActor>> Corpses;

	/** A sleeping ragdoll costs almost nothing on the CPU; the cap bounds skinned-mesh draw cost and physics wake-ups. */
	static constexpr int32 MaxCorpses = 16;
};
