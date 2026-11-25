// See KochHealthComponent.h.

#include "Combat/KochHealthComponent.h"
#include "Components/SkinnedMeshComponent.h"
#include "Engine/DamageEvents.h"

UKochHealthComponent::UKochHealthComponent()
{
	PrimaryComponentTick.bCanEverTick = false;

	ZoneDamageMultipliers.Add(EKochHitZone::Head, 4.0f);
	ZoneDamageMultipliers.Add(EKochHitZone::Torso, 1.0f);
	ZoneDamageMultipliers.Add(EKochHitZone::Arm, 0.5f);
	ZoneDamageMultipliers.Add(EKochHitZone::Leg, 0.5f);

	BoneZones.Add(FName("head"), EKochHitZone::Head);
	BoneZones.Add(FName("neck_01"), EKochHitZone::Head);
	BoneZones.Add(FName("pelvis"), EKochHitZone::Torso);
	BoneZones.Add(FName("upperarm_l"), EKochHitZone::Arm);
	BoneZones.Add(FName("upperarm_r"), EKochHitZone::Arm);
	BoneZones.Add(FName("thigh_l"), EKochHitZone::Leg);
	BoneZones.Add(FName("thigh_r"), EKochHitZone::Leg);
}

void UKochHealthComponent::BeginPlay()
{
	Super::BeginPlay();

	Health = MaxHealth;
}

float UKochHealthComponent::HandleDamage(float Damage, const FDamageEvent& DamageEvent, AController* EventInstigator)
{
	if (bDead || Damage <= 0.0f)
	{
		return 0.0f;
	}

	FKochDamageInfo Info;
	Info.Instigator = EventInstigator;

	if (DamageEvent.IsOfType(FPointDamageEvent::ClassID))
	{
		const FPointDamageEvent& Point = static_cast<const FPointDamageEvent&>(DamageEvent);
		Info.BoneName = Point.HitInfo.BoneName;
		Info.HitLocation = Point.HitInfo.ImpactPoint;
		Info.ShotDirection = Point.ShotDirection;
		Info.Zone = FindZone(Cast<USkinnedMeshComponent>(Point.HitInfo.GetComponent()), Info.BoneName);
	}
	else
	{
		Info.HitLocation = GetOwner()->GetActorLocation();
	}

	const float* Multiplier = ZoneDamageMultipliers.Find(Info.Zone);
	Info.Damage = Damage * (Multiplier ? *Multiplier : 1.0f);

	Health = FMath::Max(Health - Info.Damage, 0.0f);
	bDead = Health <= 0.0f;
	Info.bKilled = bDead;

	OnDamaged.Broadcast(Info);

	return Info.Damage;
}

EKochHitZone UKochHealthComponent::FindZone(const USkinnedMeshComponent* Mesh, FName BoneName) const
{
	// pelvis is mapped, so on the default skeletons every bone resolves before the root
	for (FName Bone = BoneName; !Bone.IsNone(); Bone = Mesh ? Mesh->GetParentBone(Bone) : NAME_None)
	{
		if (const EKochHitZone* Zone = BoneZones.Find(Bone))
		{
			return *Zone;
		}
	}

	return EKochHitZone::None;
}
