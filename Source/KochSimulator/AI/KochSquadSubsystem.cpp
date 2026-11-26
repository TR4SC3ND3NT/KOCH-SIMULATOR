// See KochSquadSubsystem.h.

#include "KochSquadSubsystem.h"
#include "KochDifficultySubsystem.h"
#include "KochEnemyCharacter.h"
#include "KochGhostTargeting.h"
#include "NavigationSystem.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "TimerManager.h"
#include "KochAwarenessComponent.h"
#include "KochSimulatorCharacter.h"
#include "Perception/AISense_Hearing.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"

namespace
{
	/** Simultaneous shooters per difficulty. */
	int32 MaxFireTokens(EKochDifficulty Difficulty)
	{
		switch (Difficulty)
		{
		case EKochDifficulty::Easy: return 2;
		case EKochDifficulty::Hard: return 4;
		default:                    return 3;
		}
	}

	/** Elroy starts when this many or fewer enemies are alive (0 = never). */
	int32 ElroyThreshold(EKochDifficulty Difficulty)
	{
		switch (Difficulty)
		{
		case EKochDifficulty::Medium: return 2;
		case EKochDifficulty::Hard:   return 3;
		default:                      return 0;
		}
	}

	/** Delay before squadmates hear a sighting callout (s). */
	float CalloutDelay(EKochDifficulty Difficulty)
	{
		switch (Difficulty)
		{
		case EKochDifficulty::Easy: return 1.2f;
		case EKochDifficulty::Hard: return 0.35f;
		default:                    return 0.7f;
		}
	}

	constexpr float FootstepInterval = 0.35f; // s, roughly one stride at run speed

	/** Navmesh projection box (cm): wide enough to catch targets on stairs/ledges. */
	const FVector NavProjectExtent(300.0, 300.0, 400.0);
}

bool UKochSquadSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

void UKochSquadSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);

	if (UKochDifficultySubsystem* DifficultySubsystem = UKochDifficultySubsystem::Get(&InWorld))
	{
		Difficulty = DifficultySubsystem->GetDifficulty();
		DifficultySubsystem->OnDifficultyChanged.AddUniqueDynamic(this, &UKochSquadSubsystem::HandleDifficultyChanged);
	}
	RestartSchedule();
	InWorld.GetTimerManager().SetTimer(FootstepTimer, this, &UKochSquadSubsystem::EmitPlayerFootsteps, FootstepInterval, true);
}

void UKochSquadSubsystem::Deinitialize()
{
	if (UKochDifficultySubsystem* DifficultySubsystem = UKochDifficultySubsystem::Get(this))
	{
		DifficultySubsystem->OnDifficultyChanged.RemoveDynamic(this, &UKochSquadSubsystem::HandleDifficultyChanged);
	}
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(PhaseTimer);
		World->GetTimerManager().ClearTimer(FootstepTimer);
	}
	Super::Deinitialize();
}

void UKochSquadSubsystem::RegisterEnemy(AKochEnemyCharacter* Enemy)
{
	if (!Enemy)
	{
		return;
	}
	Enemies.AddUnique(Enemy);
	Enemy->OnPawnDeath.AddUniqueDynamic(this, &UKochSquadSubsystem::HandleEnemyDied);
	UpdateElroy();
}

void UKochSquadSubsystem::UnregisterEnemy(AKochEnemyCharacter* Enemy)
{
	if (!Enemy)
	{
		return;
	}
	Enemy->OnPawnDeath.RemoveDynamic(this, &UKochSquadSubsystem::HandleEnemyDied);
	Enemies.Remove(Enemy);
	ReleaseFireToken(Enemy);
	UpdateElroy();
}

int32 UKochSquadSubsystem::GetAliveCount() const
{
	int32 Alive = 0;
	for (const TWeakObjectPtr<AKochEnemyCharacter>& Enemy : Enemies)
	{
		Alive += (Enemy.IsValid() && Enemy->IsAlive()) ? 1 : 0;
	}
	return Alive;
}

void UKochSquadSubsystem::HandleEnemyDied()
{
	UpdateElroy();
}

void UKochSquadSubsystem::UpdateElroy()
{
	const int32 Threshold = ElroyThreshold(Difficulty);
	const int32 Alive = GetAliveCount();
	const bool bNewElroy = Threshold > 0 && Alive > 0 && Alive <= Threshold;
	if (bNewElroy == bElroy)
	{
		return;
	}
	bElroy = bNewElroy;
	for (const TWeakObjectPtr<AKochEnemyCharacter>& Enemy : Enemies)
	{
		if (Enemy.IsValid())
		{
			const EKochGhostRole Role = Enemy->GetRole();
			Enemy->SetElroy(bElroy && (Role == EKochGhostRole::Chaser || Role == EKochGhostRole::Peeker));
		}
	}
}

void UKochSquadSubsystem::HandleDifficultyChanged(EKochDifficulty NewDifficulty)
{
	Difficulty = NewDifficulty;
	bElroy = false;
	UpdateElroy();
	RestartSchedule();
}

void UKochSquadSubsystem::RestartSchedule()
{
	PhaseStep = -1;
	AdvancePhase();
}

void UKochSquadSubsystem::AdvancePhase()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	const TConstArrayView<float> Schedule = KochGhost::GetPhaseSchedule(Difficulty);
	PhaseStep = FMath::Min(PhaseStep + 1, Schedule.Num() - 1);
	SetPhase(KochGhost::PhaseForStep(PhaseStep));

	const float Duration = Schedule[PhaseStep];
	if (Duration > 0.0f)
	{
		World->GetTimerManager().SetTimer(PhaseTimer, this, &UKochSquadSubsystem::AdvancePhase, Duration, false);
	}
	else
	{
		World->GetTimerManager().ClearTimer(PhaseTimer);
	}
}

void UKochSquadSubsystem::SetPhase(EKochSquadPhase NewPhase)
{
	Phase = NewPhase;
	++PhaseSerial; // also bumps on a restart so everyone re-paths
}

const AKochEnemyCharacter* UKochSquadSubsystem::FindLeaderFor(const AKochEnemyCharacter& Enemy) const
{
	// Nearest living Chaser; Peeker (Donk) if no Chaser is left.
	const AKochEnemyCharacter* Best = nullptr;
	double BestDistSq = TNumericLimits<double>::Max();
	bool bBestIsChaser = false;
	for (const TWeakObjectPtr<AKochEnemyCharacter>& Weak : Enemies)
	{
		const AKochEnemyCharacter* Other = Weak.Get();
		if (!Other || Other == &Enemy || !Other->IsAlive())
		{
			continue;
		}
		const EKochGhostRole Role = Other->GetRole();
		if (Role != EKochGhostRole::Chaser && Role != EKochGhostRole::Peeker)
		{
			continue;
		}
		const bool bIsChaser = Role == EKochGhostRole::Chaser;
		const double DistSq = FVector::DistSquared(Other->GetActorLocation(), Enemy.GetActorLocation());
		if ((bIsChaser && !bBestIsChaser) || (bIsChaser == bBestIsChaser && DistSq < BestDistSq))
		{
			Best = Other;
			BestDistSq = DistSq;
			bBestIsChaser = bIsChaser;
		}
	}
	return Best;
}

bool UKochSquadSubsystem::ComputeMoveTarget(const AKochEnemyCharacter& Enemy, const FKochTargetBelief& Belief, FVector& OutLocation) const
{
	// Easy: no squad tactics, everybody heads straight for the last known position.
	const EKochGhostRole Role = (Difficulty == EKochDifficulty::Easy) ? EKochGhostRole::Chaser : Enemy.GetRole();

	FKochRoleTargetInput In;
	In.PlayerLocation = Belief.Location;
	In.PlayerVelocity = Belief.Velocity;
	In.PlayerForward = Belief.Forward;
	In.SelfLocation = Enemy.GetActorLocation();
	In.AnchorLocation = Enemy.GetAnchorLocation();
	In.Phase = Enemy.IsElroy() ? EKochSquadPhase::Chase : Phase;
	if (const AKochEnemyCharacter* Leader = (Role == EKochGhostRole::Flanker) ? FindLeaderFor(Enemy) : nullptr)
	{
		In.LeaderLocation = Leader->GetActorLocation();
		In.bHasLeader = true;
	}

	OutLocation = KochGhost::ComputeRoleTarget(Role, In, TargetParams);

	if (const UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld()))
	{
		FNavLocation Projected;
		if (Nav->ProjectPointToNavigation(OutLocation, Projected, NavProjectExtent))
		{
			OutLocation = Projected.Location;
			return true;
		}
	}
	return false;
}

void UKochSquadSubsystem::ReportSighting(const AKochEnemyCharacter* Reporter, AActor* Target, const FVector& Location, const FVector& Velocity, double TimeSeen)
{
	UWorld* World = GetWorld();
	if (!World || !Target)
	{
		return;
	}
	TArray<TWeakObjectPtr<AKochEnemyCharacter>> Listeners;
	for (const TWeakObjectPtr<AKochEnemyCharacter>& Enemy : Enemies)
	{
		if (Enemy.IsValid() && Enemy.Get() != Reporter && Enemy->IsAlive())
		{
			Listeners.Add(Enemy);
		}
	}
	if (Listeners.IsEmpty())
	{
		return;
	}

	TWeakObjectPtr<AActor> WeakTarget = Target;
	FTimerHandle Handle; // one-shot; the lambda owns everything it needs
	World->GetTimerManager().SetTimer(Handle, FTimerDelegate::CreateWeakLambda(this,
		[Listeners = MoveTemp(Listeners), WeakTarget, Location, Velocity, TimeSeen]()
		{
			for (const TWeakObjectPtr<AKochEnemyCharacter>& Listener : Listeners)
			{
				if (Listener.IsValid() && Listener->IsAlive() && WeakTarget.IsValid())
				{
					Listener->GetAwareness()->ReceiveCallout(WeakTarget.Get(), Location, Velocity, TimeSeen);
				}
			}
		}), CalloutDelay(Difficulty), false);
}

bool UKochSquadSubsystem::IsSpotTaken(const FVector& Location, const AKochEnemyCharacter* Exclude, float Radius) const
{
	const double RadiusSq = FMath::Square(Radius);
	for (const TWeakObjectPtr<AKochEnemyCharacter>& Weak : Enemies)
	{
		const AKochEnemyCharacter* Other = Weak.Get();
		if (!Other || Other == Exclude || !Other->IsAlive())
		{
			continue;
		}
		if (FVector::DistSquared2D(Other->GetAwareness()->GetMoveGoal(), Location) < RadiusSq ||
			FVector::DistSquared2D(Other->GetActorLocation(), Location) < RadiusSq)
		{
			return true;
		}
	}
	return false;
}

void UKochSquadSubsystem::EmitPlayerFootsteps()
{
	if (Enemies.IsEmpty())
	{
		return;
	}
	ACharacter* Player = UGameplayStatics::GetPlayerCharacter(this, 0);
	const UCharacterMovementComponent* Move = Player ? Player->GetCharacterMovement() : nullptr;
	if (!Move || !Move->IsMovingOnGround() || Player->bIsCrouched)
	{
		return;
	}
	if (const AKochSimulatorCharacter* KochPlayer = Cast<AKochSimulatorCharacter>(Player); KochPlayer && KochPlayer->IsWalking())
	{
		return; // CS rule: walking is silent
	}
	const float Speed = Player->GetVelocity().Size2D();
	if (Speed < FootstepSpeedRatio * Move->MaxWalkSpeed)
	{
		return;
	}
	static const FName FootstepNoiseTag(TEXT("Footstep")); // must match UKochAwarenessComponent
	UAISense_Hearing::ReportNoiseEvent(this, Player->GetActorLocation(), 1.0f, Player, FootstepRange, FootstepNoiseTag);
}

bool UKochSquadSubsystem::TryAcquireFireToken(const AKochEnemyCharacter* Enemy)
{
	if (!Enemy)
	{
		return false;
	}
	FireTokenHolders.RemoveAll([](const TWeakObjectPtr<const AKochEnemyCharacter>& Holder)
	{
		return !Holder.IsValid() || !Holder->IsAlive();
	});
	if (FireTokenHolders.Contains(Enemy))
	{
		return true;
	}
	if (FireTokenHolders.Num() >= MaxFireTokens(Difficulty))
	{
		return false;
	}
	FireTokenHolders.Add(Enemy);
	return true;
}

void UKochSquadSubsystem::ReleaseFireToken(const AKochEnemyCharacter* Enemy)
{
	FireTokenHolders.Remove(Enemy);
}
