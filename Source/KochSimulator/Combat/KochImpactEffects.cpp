// See KochImpactEffects.h.

#include "Combat/KochImpactEffects.h"
#include "Components/DecalComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Engine/HitResult.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Sound/SoundBase.h"

namespace
{
	/** Random entry, or null for an empty list. */
	UMaterialInterface* PickDecal(const TArray<TObjectPtr<UMaterialInterface>>& Decals)
	{
		return Decals.Num() > 0 ? Decals[FMath::RandHelper(Decals.Num())].Get() : nullptr;
	}
}

const FKochImpactEffect& UKochImpactEffectSet::FindEffect(EKochSurface Surface) const
{
	const FKochImpactEffect* Found = Surfaces.Find(Surface);
	return Found ? *Found : Default;
}

bool UKochImpactSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

void UKochImpactSubsystem::PlayImpact(const UKochImpactEffectSet& Effects, const FHitResult& Hit, const FVector& ShotDirection, EKochSurface Surface)
{
	UWorld* World = GetWorld();
	const FKochImpactEffect& Effect = Effects.FindEffect(Surface);
	const FVector Location = Hit.ImpactPoint;

	if (Effect.Particles)
	{
		// pooled: a rifle fires 10 of these a second
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(World, Effect.Particles, Location, Hit.ImpactNormal.Rotation(), FVector::OneVector, true, true, ENCPoolMethod::AutoRelease);
	}

	if (Effect.Sound)
	{
		UGameplayStatics::PlaySoundAtLocation(World, Effect.Sound, Location, FRotator::ZeroRotator);
	}

	if (UMaterialInterface* Decal = PickDecal(Effect.Decals))
	{
		SpawnDecal(Decal, FMath::FRandRange(Effect.DecalRadius.X, Effect.DecalRadius.Y), Hit.GetComponent(), Hit.BoneName, Location, Hit.ImpactNormal);
	}

	UMaterialInterface* Splatter = Surface == EKochSurface::Flesh ? PickDecal(Effects.BloodSplatterDecals) : nullptr;
	if (Splatter)
	{
		// spray leaves along the shot, sagging a little; it lands on the first non-pawn surface behind the victim
		FHitResult Behind;
		const FCollisionQueryParams Params(SCENE_QUERY_STAT(KochBloodSplatter), true, Hit.GetActor());
		const FVector SprayDirection = (ShotDirection + FVector(0.0, 0.0, -0.15)).GetSafeNormal();
		if (World->LineTraceSingleByChannel(Behind, Location, Location + SprayDirection * Effects.BloodSplatterDistance, Koch::BulletChannel, Params)
			&& !Cast<APawn>(Behind.GetActor()))
		{
			SpawnDecal(Splatter, FMath::FRandRange(Effects.BloodSplatterRadius.X, Effects.BloodSplatterRadius.Y), Behind.GetComponent(), Behind.BoneName, Behind.ImpactPoint, Behind.ImpactNormal);
		}
	}
}

void UKochImpactSubsystem::SpawnBloodPool(const UKochImpactEffectSet& Effects, const FVector& Location, const AActor* IgnoredActor)
{
	UMaterialInterface* PoolDecal = PickDecal(Effects.BloodPoolDecals);
	if (!PoolDecal)
	{
		return;
	}

	FHitResult Ground;
	const FCollisionQueryParams Params(SCENE_QUERY_STAT(KochBloodPool), true, IgnoredActor);
	if (!GetWorld()->LineTraceSingleByChannel(Ground, Location, Location - FVector(0.0, 0.0, 150.0), Koch::BulletChannel, Params) || Cast<APawn>(Ground.GetActor()))
	{
		return;
	}

	if (UDecalComponent* Pool = SpawnDecal(PoolDecal, FMath::FRandRange(Effects.BloodPoolRadius.X, Effects.BloodPoolRadius.Y), Ground.GetComponent(), Ground.BoneName, Ground.ImpactPoint, Ground.ImpactNormal))
	{
		Pool->SetFadeIn(0.0f, Effects.BloodPoolFadeIn);
	}
}

UDecalComponent* UKochImpactSubsystem::SpawnDecal(UMaterialInterface* Material, float Radius, UPrimitiveComponent* OnComponent, FName BoneName, const FVector& Location, const FVector& Normal)
{
	// a decal projects along its local +X; random roll hides the repeat
	FRotator Rotation = (-Normal).Rotation();
	Rotation.Roll = FMath::FRandRange(-180.0f, 180.0f);
	const FVector Size(DecalDepth, Radius, Radius);

	UDecalComponent* Decal = (OnComponent && OnComponent->Mobility == EComponentMobility::Movable)
		? UGameplayStatics::SpawnDecalAttached(Material, Size, OnComponent, BoneName, Location, Rotation, EAttachLocation::KeepWorldPosition)
		: UGameplayStatics::SpawnDecalAtLocation(GetWorld(), Material, Size, Location, Rotation);
	if (!Decal)
	{
		return nullptr;
	}

	// stop drawing once it covers under ~0.1 % of the screen
	Decal->SetFadeScreenSize(0.001f);

	if (Decals.Num() < MaxDecals)
	{
		Decals.Add(Decal);
	}
	else
	{
		if (UDecalComponent* Oldest = Decals[NextDecal].Get())
		{
			Oldest->DestroyComponent();
		}
		Decals[NextDecal] = Decal;
		NextDecal = (NextDecal + 1) % MaxDecals;
	}

	return Decal;
}
