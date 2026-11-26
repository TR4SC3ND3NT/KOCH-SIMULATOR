// See KochAwarenessComponent.h.

#include "KochAwarenessComponent.h"
#include "KochEnemyCharacter.h"
#include "KochSquadSubsystem.h"
#include "AIController.h"
#include "Perception/AIPerceptionComponent.h"
#include "Perception/AISense_Sight.h"
#include "Perception/AISense_Hearing.h"
#include "Perception/AISenseConfig_Sight.h"
#include "Perception/AISenseConfig_Hearing.h"
#include "NavigationSystem.h"
#include "Engine/World.h"
#include "CollisionQueryParams.h"
#include "TimerManager.h"

namespace
{
	const FName FootstepTag(TEXT("Footstep"));
	constexpr float GoalChangeThreshold = 100.0f;  // cm; smaller goal changes don't re-path
	constexpr float ArriveRadius = 200.0f;         // cm; "reached" for hunt / search points
	constexpr float AlertNoticeScale = 0.35f;      // already-alert enemies notice ~3x faster
	constexpr float TargetEyeOffset = 60.0f;       // cm above the target's actor location (chest/head)
}

UKochAwarenessComponent::UKochAwarenessComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UKochAwarenessComponent::BeginPlay()
{
	Super::BeginPlay();
	MoveGoal = GetOwner()->GetActorLocation();
	GetWorld()->GetTimerManager().SetTimer(ThinkTimer, this, &UKochAwarenessComponent::Think, ThinkInterval, true,
		FMath::FRandRange(0.0f, ThinkInterval)); // stagger enemies across frames
}

void UKochAwarenessComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	Unbind();
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(ThinkTimer);
	}
	Super::EndPlay(EndPlayReason);
}

AKochEnemyCharacter* UKochAwarenessComponent::GetEnemy() const
{
	return Cast<AKochEnemyCharacter>(GetOwner());
}

float UKochAwarenessComponent::GetKnowledgeAge() const
{
	return static_cast<float>(GetWorld()->GetTimeSeconds() - LastSeenTime);
}

////////////////////////////////////////////////////////////////////
// Perception

void UKochAwarenessComponent::BindToController(AAIController* Controller)
{
	Unbind();
	UAIPerceptionComponent* NewPerception = Controller ? Controller->FindComponentByClass<UAIPerceptionComponent>() : nullptr;
	if (!NewPerception)
	{
		return;
	}
	Perception = NewPerception;
	NewPerception->OnTargetPerceptionUpdated.AddUniqueDynamic(this, &UKochAwarenessComponent::HandlePerceptionUpdated);
	ApplyPerceptionTuning();
}

void UKochAwarenessComponent::Unbind()
{
	if (UAIPerceptionComponent* Old = Perception.Get())
	{
		Old->OnTargetPerceptionUpdated.RemoveDynamic(this, &UKochAwarenessComponent::HandlePerceptionUpdated);
	}
	Perception.Reset();
	bInSight = false;
}

void UKochAwarenessComponent::ApplyPerceptionTuning()
{
	UAIPerceptionComponent* PerceptionComp = Perception.Get();
	const AKochEnemyCharacter* Enemy = GetEnemy();
	if (!PerceptionComp || !Enemy)
	{
		return;
	}
	const FKochEnemyTuning& Tuning = Enemy->GetActiveTuning();

	// Reuse the BP-authored configs when present so other settings (max age, etc.) survive.
	UAISenseConfig_Sight* Sight = Cast<UAISenseConfig_Sight>(PerceptionComp->GetSenseConfig(UAISense::GetSenseID<UAISense_Sight>()));
	if (!Sight)
	{
		Sight = NewObject<UAISenseConfig_Sight>(PerceptionComp);
	}
	Sight->SightRadius = Tuning.SightRange;
	Sight->LoseSightRadius = Tuning.SightRange * 1.15f;
	Sight->PeripheralVisionAngleDegrees = Tuning.SightHalfAngle;
	Sight->DetectionByAffiliation.bDetectEnemies = true;
	Sight->DetectionByAffiliation.bDetectNeutrals = true; // the player has no team interface; filtered by TargetTag
	Sight->DetectionByAffiliation.bDetectFriendlies = true;
	PerceptionComp->ConfigureSense(*Sight);

	UAISenseConfig_Hearing* Hearing = Cast<UAISenseConfig_Hearing>(PerceptionComp->GetSenseConfig(UAISense::GetSenseID<UAISense_Hearing>()));
	if (!Hearing)
	{
		Hearing = NewObject<UAISenseConfig_Hearing>(PerceptionComp);
	}
	Hearing->HearingRange = Tuning.HearingRange;
	Hearing->DetectionByAffiliation.bDetectEnemies = true;
	Hearing->DetectionByAffiliation.bDetectNeutrals = true;
	Hearing->DetectionByAffiliation.bDetectFriendlies = true;
	Hearing->SetMaxAge(3.0f);
	PerceptionComp->ConfigureSense(*Hearing);
}

void UKochAwarenessComponent::HandlePerceptionUpdated(AActor* Actor, FAIStimulus Stimulus)
{
	if (!Actor || !Actor->ActorHasTag(TargetTag))
	{
		return;
	}
	const double Now = GetWorld()->GetTimeSeconds();

	if (Stimulus.Type == UAISense::GetSenseID<UAISense_Sight>())
	{
		Target = Actor;
		bInSight = Stimulus.WasSuccessfullySensed();
		if (!bInSight)
		{
			// Lost sight: remember where he was last seen (not where he is now).
			LastKnownLocation = Stimulus.StimulusLocation;
			LastSeenTime = Now;
		}
		return;
	}

	if (Stimulus.Type == UAISense::GetSenseID<UAISense_Hearing>() && Stimulus.WasSuccessfullySensed())
	{
		Target = Actor;
		const bool bFootstep = Stimulus.Tag == FootstepTag;
		switch (State)
		{
		case EKochAwareness::Unaware:
			if (bFootstep)
			{
				NoiseLocation = Stimulus.StimulusLocation;
				SetState(EKochAwareness::Suspicious);
				break;
			}
			// Gunfire: treat as a sighting of the shooter's area.
			[[fallthrough]];
		case EKochAwareness::Suspicious:
		case EKochAwareness::Search:
			LastKnownLocation = Stimulus.StimulusLocation;
			LastKnownVelocity = FVector::ZeroVector;
			LastSeenTime = Now;
			SetState(EKochAwareness::Hunt);
			break;
		case EKochAwareness::Hunt:
			// Fresher information while hunting.
			LastKnownLocation = Stimulus.StimulusLocation;
			LastSeenTime = Now;
			break;
		case EKochAwareness::Engage:
		default:
			break;
		}
	}
}

void UKochAwarenessComponent::ReceiveCallout(AActor* InTarget, const FVector& Location, const FVector& Velocity, double TimeSeen)
{
	if (!InTarget || bInSight || TimeSeen <= LastSeenTime)
	{
		return;
	}
	Target = InTarget;
	LastKnownLocation = Location;
	LastKnownVelocity = Velocity;
	LastSeenTime = TimeSeen;
	if (State != EKochAwareness::Engage)
	{
		SetState(EKochAwareness::Hunt);
	}
}

////////////////////////////////////////////////////////////////////
// State machine

void UKochAwarenessComponent::SetState(EKochAwareness NewState)
{
	if (State == NewState)
	{
		return;
	}
	State = NewState;
	StateEnterTime = GetWorld()->GetTimeSeconds();
	NextEngageEvalTime = 0.0;
	if (NewState == EKochAwareness::Search)
	{
		BuildSearchPoints();
	}
	UpdateGoal(StateEnterTime);
	++GoalSerial; // every state change re-paths
}

void UKochAwarenessComponent::Think()
{
	AKochEnemyCharacter* Enemy = GetEnemy();
	if (!Enemy || !Enemy->IsAlive())
	{
		return;
	}
	const double Now = GetWorld()->GetTimeSeconds();
	const FKochEnemyTuning& Tuning = Enemy->GetActiveTuning();
	AActor* TargetActor = Target.Get();

	// While visible we may read the true position: he is in plain sight.
	if (bInSight && TargetActor)
	{
		LastKnownLocation = TargetActor->GetActorLocation();
		LastKnownVelocity = TargetActor->GetVelocity();
		LastSeenTime = Now;

		const float Dist = FVector::Dist(Enemy->GetActorLocation(), LastKnownLocation);
		const float CloseBoost = FMath::Clamp(1.5f - Dist / FMath::Max(Tuning.SightRange, 1.0f), 0.5f, 1.5f);
		Exposure += ThinkInterval * CloseBoost;
	}
	else
	{
		Exposure = FMath::Max(0.0f, Exposure - ThinkInterval * 0.5f);
	}

	const bool bAlert = State == EKochAwareness::Hunt || State == EKochAwareness::Search || State == EKochAwareness::Suspicious;
	const float NoticeNeeded = Tuning.NoticeTime * (bAlert ? AlertNoticeScale : 1.0f);
	const float StateAge = static_cast<float>(Now - StateEnterTime);
	const float KnowledgeAge = static_cast<float>(Now - LastSeenTime);

	switch (State)
	{
	case EKochAwareness::Unaware:
	case EKochAwareness::Suspicious:
	case EKochAwareness::Hunt:
	case EKochAwareness::Search:
		if (bInSight && Exposure >= NoticeNeeded)
		{
			SetState(EKochAwareness::Engage);
			break;
		}
		if (State == EKochAwareness::Suspicious && StateAge > SuspiciousTime)
		{
			SetState(EKochAwareness::Unaware);
		}
		else if (State == EKochAwareness::Hunt)
		{
			const bool bReachedLastKnown = FVector::Dist2D(Enemy->GetActorLocation(), LastKnownLocation) < ArriveRadius;
			if (KnowledgeAge > Tuning.MemoryTime || bReachedLastKnown)
			{
				SetState(EKochAwareness::Search);
			}
		}
		else if (State == EKochAwareness::Search && (SearchPoints.IsEmpty() || StateAge > Tuning.SearchTime))
		{
			SetState(EKochAwareness::Unaware);
		}
		break;

	case EKochAwareness::Engage:
		if (!bInSight && KnowledgeAge > Tuning.LoseSightGrace)
		{
			SetState(EKochAwareness::Hunt);
		}
		break;
	}

	// Radio the squad while we can see him (at most once a second).
	if (State == EKochAwareness::Engage && bInSight && TargetActor && Now - LastCalloutTime >= 1.0)
	{
		LastCalloutTime = Now;
		if (UKochSquadSubsystem* Squad = GetWorld()->GetSubsystem<UKochSquadSubsystem>())
		{
			Squad->ReportSighting(Enemy, TargetActor, LastKnownLocation, LastKnownVelocity, Now);
		}
	}

	UpdateGoal(Now);
}

FKochTargetBelief UKochAwarenessComponent::MakeBelief(double Now) const
{
	// Extrapolate at most 1 s from the last sighting; older velocity is meaningless.
	const float Age = static_cast<float>(Now - LastSeenTime);
	FKochTargetBelief Belief;
	Belief.Velocity = (Age < 2.0f) ? LastKnownVelocity : FVector::ZeroVector;
	Belief.Location = LastKnownLocation + Belief.Velocity * FMath::Min(Age, 1.0f);
	const FVector Flat(Belief.Velocity.X, Belief.Velocity.Y, 0.0);
	Belief.Forward = Flat.IsNearlyZero(10.0) ? (LastKnownLocation - GetOwner()->GetActorLocation()).GetSafeNormal2D() : Flat.GetSafeNormal();
	return Belief;
}

void UKochAwarenessComponent::UpdateGoal(double Now)
{
	const AKochEnemyCharacter* Enemy = GetEnemy();
	if (!Enemy)
	{
		return;
	}

	switch (State)
	{
	case EKochAwareness::Unaware:
		SetGoal(Enemy->GetAnchorLocation());
		break;

	case EKochAwareness::Suspicious:
		SetGoal(NoiseLocation);
		break;

	case EKochAwareness::Hunt:
	{
		FVector Goal = LastKnownLocation;
		if (const UKochSquadSubsystem* Squad = GetWorld()->GetSubsystem<UKochSquadSubsystem>())
		{
			Squad->ComputeMoveTarget(*Enemy, MakeBelief(Now), Goal);
		}
		SetGoal(Goal);
		break;
	}

	case EKochAwareness::Engage:
		if (Now >= NextEngageEvalTime)
		{
			NextEngageEvalTime = Now + EngagePositionInterval;
			FVector Goal;
			if (const AActor* TargetActor = Target.Get(); TargetActor && FindEngagePosition(*TargetActor, Goal))
			{
				SetGoal(Goal);
			}
		}
		break;

	case EKochAwareness::Search:
		while (!SearchPoints.IsEmpty() && FVector::Dist2D(Enemy->GetActorLocation(), SearchPoints[0]) < ArriveRadius)
		{
			SearchPoints.RemoveAt(0);
		}
		if (!SearchPoints.IsEmpty())
		{
			SetGoal(SearchPoints[0]);
		}
		break;
	}
}

void UKochAwarenessComponent::SetGoal(const FVector& NewGoal, bool bForce)
{
	if (bForce || FVector::DistSquared(NewGoal, MoveGoal) > FMath::Square(GoalChangeThreshold))
	{
		MoveGoal = NewGoal;
		++GoalSerial;
	}
}

void UKochAwarenessComponent::BuildSearchPoints()
{
	SearchPoints.Reset();
	SearchPoints.Add(LastKnownLocation); // first: where he was last seen
	const UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());
	if (!Nav)
	{
		return;
	}
	for (int32 i = 0; i < SearchPointCount; ++i)
	{
		FNavLocation Point;
		if (Nav->GetRandomReachablePointInRadius(LastKnownLocation, SearchRadius, Point))
		{
			SearchPoints.Add(Point.Location);
		}
	}
}

bool UKochAwarenessComponent::FindEngagePosition(const AActor& InTarget, FVector& OutLocation) const
{
	// Sample a ring of nav points around us; keep ones that see the target, sit in the engage band,
	// are close to travel to and not on top of a squadmate. ~2 traces per sample, 1x per EngagePositionInterval.
	const AKochEnemyCharacter* Enemy = GetEnemy();
	const UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());
	if (!Enemy || !Nav)
	{
		return false;
	}
	const UKochSquadSubsystem* Squad = GetWorld()->GetSubsystem<UKochSquadSubsystem>();
	const FKochEnemyTuning& Tuning = Enemy->GetActiveTuning();
	const FVector Self = Enemy->GetActorLocation();
	const FVector TargetEye = InTarget.GetActorLocation() + FVector(0.0, 0.0, TargetEyeOffset);
	const float EyeHeight = Enemy->BaseEyeHeight * Enemy->GetActorScale3D().Z;
	const float CrouchHeight = EyeHeight * 0.45f;

	FCollisionQueryParams Params(SCENE_QUERY_STAT(KochEngagePosition), false, Enemy);
	Params.AddIgnoredActor(&InTarget);

	constexpr int32 NumAngles = 8;
	constexpr float Radii[] = { 0.0f, 350.0f, 700.0f };
	const float MidRange = 0.5f * (Tuning.EngageRangeMin + Tuning.EngageRangeMax);

	float BestScore = -TNumericLimits<float>::Max();
	bool bFound = false;
	for (const float Radius : Radii)
	{
		const int32 Count = (Radius <= 0.0f) ? 1 : NumAngles;
		for (int32 i = 0; i < Count; ++i)
		{
			const float Angle = (2.0f * PI * i) / Count;
			const FVector Probe = Self + FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.0) * Radius;
			FNavLocation NavPoint;
			if (!Nav->ProjectPointToNavigation(Probe, NavPoint, FVector(100.0, 100.0, 250.0)))
			{
				continue;
			}
			const FVector Point = NavPoint.Location;

			// Must be able to shoot from here (standing eye -> target).
			if (GetWorld()->LineTraceTestByChannel(Point + FVector(0.0, 0.0, EyeHeight), TargetEye, ECC_Visibility, Params))
			{
				continue;
			}

			const float Dist = FVector::Dist2D(Point, TargetEye);
			float Score = -FMath::Abs(Dist - MidRange) * 0.01f;
			if (Dist < Tuning.EngageRangeMin)
			{
				Score -= (Tuning.EngageRangeMin - Dist) * 0.03f; // too close: very bad
			}
			Score -= FVector::Dist2D(Point, Self) * 0.004f;    // prefer short moves

			// Low cover: target cannot see our crouched body from here.
			if (GetWorld()->LineTraceTestByChannel(TargetEye, Point + FVector(0.0, 0.0, CrouchHeight), ECC_Visibility, Params))
			{
				Score += 4.0f;
			}
			if (Squad && Squad->IsSpotTaken(Point, Enemy, 250.0f))
			{
				Score -= 6.0f;
			}

			if (Score > BestScore)
			{
				BestScore = Score;
				OutLocation = Point;
				bFound = true;
			}
		}
	}
	return bFound;
}
