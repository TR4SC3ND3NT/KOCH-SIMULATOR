// Kill events for the CS-style kill feed: deaths call ReportDeath, UI (UKochKillFeedWidget) listens to OnKill.
// Resolves killer/victim names, the killer's weapon icon and headshots. No UI code here.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "KochKillFeedSubsystem.generated.h"

class UTexture2D;
class AController;
struct FDamageEvent;

/** One kill-feed line: "Killer [weapon] (headshot) Victim". */
USTRUCT(BlueprintType)
struct FKochKillInfo
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Koch|KillFeed")
	FText KillerName;

	UPROPERTY(BlueprintReadOnly, Category = "Koch|KillFeed")
	FText VictimName;

	/** Killer's weapon icon; null for suicides / unknown damage. */
	UPROPERTY(BlueprintReadOnly, Category = "Koch|KillFeed")
	TObjectPtr<UTexture2D> WeaponIcon;

	UPROPERTY(BlueprintReadOnly, Category = "Koch|KillFeed")
	bool bHeadshot = false;

	/** Side flags pick the name colours (player = friendly, everyone else = hostile). */
	UPROPERTY(BlueprintReadOnly, Category = "Koch|KillFeed")
	bool bKillerIsPlayer = false;

	UPROPERTY(BlueprintReadOnly, Category = "Koch|KillFeed")
	bool bVictimIsPlayer = false;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FKochKillDelegate, const FKochKillInfo&, Kill);

UCLASS()
class KOCHSIMULATOR_API UKochKillFeedSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	/** Call once when Victim dies, with the arguments of the killing TakeDamage. Safe with null instigator/causer. */
	static void ReportDeath(AActor* Victim, const FDamageEvent& DamageEvent, AController* EventInstigator, AActor* DamageCauser);

	/** Bone name the projectile puts in FPointDamageEvent::HitInfo for head hits. */
	static const FName HeadshotBone;

	UPROPERTY(BlueprintAssignable, Category = "Koch|KillFeed")
	FKochKillDelegate OnKill;

protected:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;

private:
	static FText GetDisplayName(const AActor* Actor);
	static bool IsPlayer(const AActor* Actor);
};
