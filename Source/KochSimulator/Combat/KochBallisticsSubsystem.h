// Simulates every bullet in the world as plain data (no actor per shot). Used by AShooterWeapon when bUseBallistics is set.
// Method: per-tick segment trace with gravity and travel time; the usual trace-projectile approach (Lyra itself is pure hitscan).

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "Combat/KochCombatTypes.h"
#include "KochBallisticsSubsystem.generated.h"

/** One bullet in flight. */
USTRUCT()
struct FKochBullet
{
	GENERATED_BODY()

	UPROPERTY()
	FKochBulletSpec Spec;

	/** Never hit by its own bullet; also the damage causer and noise instigator. */
	UPROPERTY()
	TWeakObjectPtr<AActor> Shooter;

	FVector Position = FVector::ZeroVector;

	/** cm/s */
	FVector Velocity = FVector::ZeroVector;

	/** cm left before the bullet is dropped. */
	float RangeLeft = 0.0f;

	/** 1 at the muzzle; penetrations lower it. Scales damage. */
	float Energy = 1.0f;

	FName NoiseTag;
};

UCLASS()
class KOCHSIMULATOR_API UKochBallisticsSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:

	/**
	 * Fires one bullet. Its first step runs inside this call, so close-range hits land in the same frame as the shot.
	 * @param Direction  unit vector
	 * @param Shooter    ignored by the bullet; its controller is the damage instigator
	 */
	void FireBullet(const FKochBulletSpec& Spec, const FVector& Start, const FVector& Direction, AActor* Shooter, FName NoiseTag = NAME_None);

	/** Bullets currently in flight. */
	int32 GetNumBullets() const { return Bullets.Num(); }

	//~Begin FTickableGameObject
	virtual void Tick(float DeltaTime) override;
	virtual bool IsTickable() const override { return Bullets.Num() > 0; }
	virtual TStatId GetStatId() const override;
	//~End FTickableGameObject

protected:

	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;

private:

	/** Advances a bullet by DeltaTime. False once it is spent. */
	bool StepBullet(FKochBullet& Bullet, float DeltaTime);

	/** Damage, physics impulse, noise and effects for one hit. True if the bullet went through; Bullet.Position is then the exit point. */
	bool HandleImpact(FKochBullet& Bullet, const FHitResult& Hit, const FVector& Direction);

	UPROPERTY(Transient)
	TArray<FKochBullet> Bullets;

	/** Bullets fired from inside a damage callback while Bullets is being stepped. */
	UPROPERTY(Transient)
	TArray<FKochBullet> PendingBullets;

	bool bStepping = false;

	/** More than this many in flight: the oldest is dropped. */
	static constexpr int32 MaxBullets = 512;

	/** Surfaces a bullet can pass through or hit in a single step. */
	static constexpr int32 MaxHitsPerStep = 4;

	/** A bullet that would leave a wall with less than this share of its energy stays inside it. */
	static constexpr float MinEnergyToExit = 0.05f;
};
