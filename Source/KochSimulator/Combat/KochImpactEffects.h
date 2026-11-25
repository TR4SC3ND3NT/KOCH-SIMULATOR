// Bullet impact effects: a data asset mapping surface -> particles/decal/sound, and the world subsystem that plays them and caps decals.
// Used by UKochBallisticsSubsystem (hits) and UKochHitReactionComponent (blood pool). Idea from Lyra's context effects (Epic sample), without GAS.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Subsystems/WorldSubsystem.h"
#include "Combat/KochCombatTypes.h"
#include "KochImpactEffects.generated.h"

class UDecalComponent;
class UMaterialInterface;
class UNiagaraSystem;
class UPrimitiveComponent;
class USoundBase;
struct FHitResult;

/** What one hit on one kind of surface looks and sounds like. Every field is optional. */
USTRUCT(BlueprintType)
struct FKochImpactEffect
{
	GENERATED_BODY()

	/** Spawned at the hit, X axis along the surface normal. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Impact")
	TObjectPtr<UNiagaraSystem> Particles;

	/** Bullet hole or wound, projected into the surface. One is picked at random per hit. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Impact")
	TArray<TObjectPtr<UMaterialInterface>> Decals;

	/** Decal radius, random between X and Y (cm). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Impact")
	FVector2D DecalRadius = FVector2D(4.0, 7.0);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Impact")
	TObjectPtr<USoundBase> Sound;
};

UCLASS(BlueprintType)
class KOCHSIMULATOR_API UKochImpactEffectSet : public UDataAsset
{
	GENERATED_BODY()

public:

	/** Used for any surface missing from Surfaces. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Impact")
	FKochImpactEffect Default;

	/** Flesh is every pawn; the other surfaces come from UKochPhysicalMaterial. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Impact")
	TMap<EKochSurface, FKochImpactEffect> Surfaces;

	/** Blood thrown onto whatever is behind a flesh hit, within BloodSplatterDistance. One is picked at random. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Blood")
	TArray<TObjectPtr<UMaterialInterface>> BloodSplatterDecals;

	/** Radius, random between X and Y (cm). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Blood")
	FVector2D BloodSplatterRadius = FVector2D(18.0, 40.0);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Blood", meta=(ClampMin=0, Units="cm"))
	float BloodSplatterDistance = 250.0f;

	/** Pool that fades in under a corpse, one picked at random. The material needs a Decal Lifetime Opacity node for the fade. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Blood")
	TArray<TObjectPtr<UMaterialInterface>> BloodPoolDecals;

	/** Radius, random between X and Y (cm). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Blood")
	FVector2D BloodPoolRadius = FVector2D(45.0, 70.0);

	/** Seconds the pool takes to appear. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Blood", meta=(ClampMin=0, Units="s"))
	float BloodPoolFadeIn = 6.0f;

	const FKochImpactEffect& FindEffect(EKochSurface Surface) const;
};

UCLASS()
class KOCHSIMULATOR_API UKochImpactSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:

	/** Particles, sound and decal for one hit; on flesh also the blood splatter behind the victim. ShotDirection is the bullet's travel direction. */
	void PlayImpact(const UKochImpactEffectSet& Effects, const FHitResult& Hit, const FVector& ShotDirection, EKochSurface Surface);

	/** Blood pool on the ground under Location (searches 150 cm down). IgnoredActor: the corpse. */
	void SpawnBloodPool(const UKochImpactEffectSet& Effects, const FVector& Location, const AActor* IgnoredActor);

protected:

	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;

private:

	/** Projects a decal into a surface; attached when the surface can move (bone, prop). Returns null if it could not be created. */
	UDecalComponent* SpawnDecal(UMaterialInterface* Material, float Radius, UPrimitiveComponent* OnComponent, FName BoneName, const FVector& Location, const FVector& Normal);

	/** Ring of live decals; weak because attached ones die with their owner. */
	TArray<TWeakObjectPtr<UDecalComponent>> Decals;

	int32 NextDecal = 0;

	/** Oldest decal is destroyed past this count. DBuffer cost follows on-screen overlap, so the cap is about memory and clutter. */
	static constexpr int32 MaxDecals = 128;

	/** Half-depth of the projection box (cm): thin, so decals do not wrap around corners. */
	static constexpr float DecalDepth = 6.0f;
};
