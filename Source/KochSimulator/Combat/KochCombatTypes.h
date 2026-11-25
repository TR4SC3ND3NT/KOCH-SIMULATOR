// Shared combat types (hit zones, surfaces, bullet spec, damage record). Used by every class in Combat/ and by AShooterWeapon.

#pragma once

#include "CoreMinimal.h"
#include "Engine/EngineTypes.h"
#include "KochCombatTypes.generated.h"

class AController;
class UDamageType;
class UKochImpactEffectSet;

namespace Koch
{
	/** Channel bullets trace on: the template's "Projectile" object channel (Config/DefaultEngine.ini). Capsules of zoned characters ignore it so the trace reaches the physics-asset bodies. */
	inline constexpr ECollisionChannel BulletChannel = ECC_GameTraceChannel1;
}

/** Body region a hit landed in; picks the damage multiplier and the hit reaction. */
UENUM(BlueprintType)
enum class EKochHitZone : uint8
{
	None,
	Head,
	Torso,
	Arm,
	Leg
};

/** What a bullet hit; picks the impact effect. Set per physical material (UKochPhysicalMaterial); anything without one is Default. */
UENUM(BlueprintType)
enum class EKochSurface : uint8
{
	Default,
	Concrete,
	Brick,
	Metal,
	Wood,
	Glass,
	Dirt,
	Grass,
	Flesh
};

/** One ammunition type, set on the weapon Blueprint. Distances in cm, speeds in cm/s. */
USTRUCT(BlueprintType)
struct FKochBulletSpec
{
	GENERATED_BODY()

	/** Muzzle velocity. 7.62x39 from an AK: ~715 m/s. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bullet", meta=(ClampMin=1000, Units="cm/s"))
	float MuzzleSpeed = 71500.0f;

	/** Damage of a torso hit at full energy; the victim's UKochHealthComponent scales it by zone. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bullet", meta=(ClampMin=0))
	float Damage = 55.0f;

	/** The bullet is dropped after this flight distance. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bullet", meta=(ClampMin=100, Units="cm"))
	float MaxRange = 80000.0f;

	/** 1 = world gravity. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bullet", meta=(ClampMin=0))
	float GravityScale = 1.0f;

	/** Scales UKochPhysicalMaterial::PenetrationDepth: 1 = rifle, ~0.4 = pistol. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bullet", meta=(ClampMin=0))
	float PenetrationPower = 1.0f;

	/** Impulse (kg*cm/s) given to simulating bodies it hits: props, spent cases, corpses. Real momentum is ~570; games exaggerate. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bullet", meta=(ClampMin=0))
	float PhysicsImpulse = 2500.0f;

	/** AI hearing: loudness and range (cm) of the impact noise. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bullet", meta=(ClampMin=0))
	float ImpactNoiseLoudness = 3.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bullet", meta=(ClampMin=0, Units="cm"))
	float ImpactNoiseRange = 1000.0f;

	/** Optional damage type (none: UDamageType). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bullet")
	TSubclassOf<UDamageType> DamageType;

	/** Impact particles, decals and sounds (none: silent, invisible hits). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bullet")
	TObjectPtr<UKochImpactEffectSet> ImpactEffects;
};

/** Recoil and spread of one weapon, set on the weapon Blueprint. Angles in degrees. Defaults suit an AK-type rifle. */
USTRUCT(BlueprintType)
struct FKochRecoilSpec
{
	GENERATED_BODY()

	/** Muzzle climb per shot. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Recoil", meta=(ClampMin=0))
	float PitchKick = 0.55f;

	/** Sideways kick per shot, random between -YawKick and +YawKick. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Recoil", meta=(ClampMin=0))
	float YawKick = 0.20f;

	/** Share of the kick that settles back by itself; the rest the player has to pull down. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Recoil", meta=(ClampMin=0, ClampMax=1))
	float RecoveryFraction = 0.7f;

	/** Seconds after the last shot before the view starts to settle. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Recoil", meta=(ClampMin=0, Units="s"))
	float RecoveryDelay = 0.12f;

	/** Settle rate (1/s): 9 returns most of it in about 0.3 s. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Recoil", meta=(ClampMin=0.1))
	float RecoverySpeed = 9.0f;

	/** Scales the fire camera shake (1 = rifle, pistols lower). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Recoil", meta=(ClampMin=0))
	float ShakeScale = 1.0f;

	/** Spread added per shot (cone half-angle), on top of the weapon's AimVariance. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Spread", meta=(ClampMin=0))
	float SpreadPerShot = 0.25f;

	/** Most spread sustained fire can add. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Spread", meta=(ClampMin=0))
	float MaxSpreadHeat = 2.5f;

	/** Degrees of added spread lost per second while not firing. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Spread", meta=(ClampMin=0))
	float SpreadCoolRate = 5.0f;
};

/** One resolved hit, broadcast by UKochHealthComponent. */
USTRUCT(BlueprintType)
struct FKochDamageInfo
{
	GENERATED_BODY()

	/** Damage applied after the zone multiplier. */
	UPROPERTY(BlueprintReadOnly, Category="Damage")
	float Damage = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Damage")
	EKochHitZone Zone = EKochHitZone::None;

	/** Bone of the physics body that was hit (None for non-point damage). */
	UPROPERTY(BlueprintReadOnly, Category="Damage")
	FName BoneName;

	/** World space. */
	UPROPERTY(BlueprintReadOnly, Category="Damage")
	FVector HitLocation = FVector::ZeroVector;

	/** Unit vector the shot travelled along (zero for non-point damage). */
	UPROPERTY(BlueprintReadOnly, Category="Damage")
	FVector ShotDirection = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category="Damage")
	TObjectPtr<AController> Instigator;

	/** True on the hit that brought health to zero. */
	UPROPERTY(BlueprintReadOnly, Category="Damage")
	bool bKilled = false;
};
