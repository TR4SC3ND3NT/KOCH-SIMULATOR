// See KochKillFeedSubsystem.h.

#include "KochKillFeedSubsystem.h"
#include "KochEnemyCharacter.h"
#include "ShooterProjectile.h"
#include "ShooterWeapon.h"
#include "Engine/DamageEvents.h"
#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerState.h"
#include "KochSimulator.h"
#include "Engine/Texture2D.h"

#define LOCTEXT_NAMESPACE "KochKillFeed"

const FName UKochKillFeedSubsystem::HeadshotBone = FName("head");

bool UKochKillFeedSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

void UKochKillFeedSubsystem::ReportDeath(AActor* Victim, const FDamageEvent& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
	UWorld* World = Victim ? Victim->GetWorld() : nullptr;
	UKochKillFeedSubsystem* Subsystem = World ? World->GetSubsystem<UKochKillFeedSubsystem>() : nullptr;
	if (!Subsystem)
	{
		return;
	}

	const AActor* Killer = EventInstigator ? EventInstigator->GetPawn() : nullptr;
	if (!Killer && DamageCauser)
	{
		Killer = DamageCauser->GetInstigator();
	}

	FKochKillInfo Kill;
	Kill.VictimName = GetDisplayName(Victim);
	Kill.bVictimIsPlayer = IsPlayer(Victim);
	Kill.KillerName = (Killer && Killer != Victim) ? GetDisplayName(Killer) : FText::GetEmpty(); // CS shows suicides with no killer
	Kill.bKillerIsPlayer = IsPlayer(Killer);

	if (const AShooterProjectile* Projectile = Cast<AShooterProjectile>(DamageCauser))
	{
		if (const AShooterWeapon* Weapon = Projectile->GetSourceWeapon())
		{
			Kill.WeaponIcon = Weapon->GetKillFeedIcon();
		}
	}
	if (DamageEvent.IsOfType(FPointDamageEvent::ClassID))
	{
		Kill.bHeadshot = static_cast<const FPointDamageEvent&>(DamageEvent).HitInfo.BoneName == HeadshotBone;
	}

	UE_LOG(LogKochSimulator, Log, TEXT("Kill: %s [%s]%s %s"), *Kill.KillerName.ToString(),
		Kill.WeaponIcon ? *Kill.WeaponIcon->GetName() : TEXT("-"), Kill.bHeadshot ? TEXT(" [headshot]") : TEXT(""), *Kill.VictimName.ToString());
	Subsystem->OnKill.Broadcast(Kill);
}

FText UKochKillFeedSubsystem::GetDisplayName(const AActor* Actor)
{
	if (const AKochEnemyCharacter* Enemy = Cast<AKochEnemyCharacter>(Actor))
	{
		return Enemy->GetDisplayName();
	}
	if (const APawn* Pawn = Cast<APawn>(Actor))
	{
		if (const APlayerState* PlayerState = Pawn->GetPlayerState(); PlayerState && !PlayerState->GetPlayerName().IsEmpty())
		{
			return FText::FromString(PlayerState->GetPlayerName());
		}
	}
	return LOCTEXT("Unknown", "Enemy");
}

bool UKochKillFeedSubsystem::IsPlayer(const AActor* Actor)
{
	const APawn* Pawn = Cast<APawn>(Actor);
	return Pawn && Pawn->IsPlayerControlled();
}

#undef LOCTEXT_NAMESPACE
