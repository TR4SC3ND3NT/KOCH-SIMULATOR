// See KochStateTreeTasks.h.

#include "KochStateTreeTasks.h"
#include "KochEnemyCharacter.h"
#include "KochSquadSubsystem.h"
#include "KochDifficultySubsystem.h"
#include "KochAwarenessComponent.h"
#include "StateTreeExecutionContext.h"
#include "AIController.h"
#include "NavigationSystem.h"
#include "Engine/World.h"

namespace
{
	UKochSquadSubsystem* GetSquad(const AActor* Actor)
	{
		const UWorld* World = Actor ? Actor->GetWorld() : nullptr;
		return World ? World->GetSubsystem<UKochSquadSubsystem>() : nullptr;
	}

	/** Snap to the navmesh within a small box (cm); returns the input if there is no navmesh there. */
	FVector ProjectToNav(const AActor* Context, const FVector& Point)
	{
		if (const UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(Context->GetWorld()))
		{
			FNavLocation Projected;
			if (Nav->ProjectPointToNavigation(Point, Projected, FVector(50.0, 50.0, 200.0)))
			{
				return Projected.Location;
			}
		}
		return Point;
	}

	/** True when the enemy moves slowly enough for an accurate CS-style shot. */
	bool IsAccurateSpeed(const AKochEnemyCharacter& Character)
	{
		const FKochEnemyTuning& Tuning = Character.GetActiveTuning();
		return Character.GetVelocity().Size2D() <= Tuning.AccurateSpeedRatio * Tuning.RunSpeed;
	}

	constexpr float ArriveTolerance = 25.0f; // cm

	/** Unbound Target input -> the player this enemy is aware of. */
	void ResolveTarget(TObjectPtr<AActor>& Target, const AKochEnemyCharacter* Character)
	{
		if (!Target && Character && Character->GetAwareness())
		{
			Target = Character->GetAwareness()->GetTarget();
		}
	}
}

////////////////////////////////////////////////////////////////////
// Awareness condition

bool FStateTreeKochAwarenessCondition::TestCondition(FStateTreeExecutionContext& Context) const
{
	const FInstanceDataType& Data = Context.GetInstanceData(*this);
	const UKochAwarenessComponent* Awareness = Data.Character ? Data.Character->GetAwareness() : nullptr;
	return Awareness && ((Awareness->GetState() == Data.State) != Data.bInvert);
}

#if WITH_EDITOR
FText FStateTreeKochAwarenessCondition::GetDescription(const FGuid& ID, FStateTreeDataView InstanceDataView, const IStateTreeBindingLookup& BindingLookup, EStateTreeNodeFormatting Formatting /*= EStateTreeNodeFormatting::Text*/) const
{
	const FInstanceDataType* Data = InstanceDataView.GetPtr<FInstanceDataType>();
	const FText StateName = Data ? StaticEnum<EKochAwareness>()->GetDisplayValueAsText(Data->State) : FText::GetEmpty();
	const bool bInvert = Data && Data->bInvert;
	return FText::Format(FText::FromString(bInvert ? "<b>Awareness is not</b> {0}" : "<b>Awareness is</b> {0}"), StateName);
}
#endif

////////////////////////////////////////////////////////////////////
// Role condition

bool FStateTreeKochRoleCondition::TestCondition(FStateTreeExecutionContext& Context) const
{
	const FInstanceDataType& Data = Context.GetInstanceData(*this);
	return Data.Character && ((Data.Character->GetRole() == Data.Role) != Data.bInvert);
}

#if WITH_EDITOR
FText FStateTreeKochRoleCondition::GetDescription(const FGuid& ID, FStateTreeDataView InstanceDataView, const IStateTreeBindingLookup& BindingLookup, EStateTreeNodeFormatting Formatting /*= EStateTreeNodeFormatting::Text*/) const
{
	const FInstanceDataType* Data = InstanceDataView.GetPtr<FInstanceDataType>();
	const FText RoleName = Data ? StaticEnum<EKochGhostRole>()->GetDisplayValueAsText(Data->Role) : FText::GetEmpty();
	const bool bInvert = Data && Data->bInvert;
	return FText::Format(FText::FromString(bInvert ? "<b>Role is not</b> {0}" : "<b>Role is</b> {0}"), RoleName);
}
#endif

////////////////////////////////////////////////////////////////////
// Move to awareness goal

namespace
{
	void MoveToGoal(FStateTreeKochMoveToGoalInstanceData& Data, const UKochAwarenessComponent& Awareness)
	{
		Data.Controller->MoveToLocation(Awareness.GetMoveGoal(), Data.AcceptanceRadius, /*bStopOnOverlap*/ true, /*bUsePathfinding*/ true,
			/*bProjectDestinationToNavigation*/ true, /*bCanStrafe*/ true);
		Data.LastGoalSerial = Awareness.GetGoalSerial();
		Data.TimeSinceMove = 0.0f;
	}
}

EStateTreeRunStatus FStateTreeKochMoveToGoalTask::EnterState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const
{
	FInstanceDataType& Data = Context.GetInstanceData(*this);
	const UKochAwarenessComponent* Awareness = Data.Character ? Data.Character->GetAwareness() : nullptr;
	if (!Awareness || !Data.Controller)
	{
		return EStateTreeRunStatus::Failed;
	}
	Data.Character->SetMoveSpeedScale(Data.SpeedScale);
	if (Data.bFaceTarget && Awareness->GetTarget())
	{
		Data.Controller->SetFocus(Awareness->GetTarget());
	}
	MoveToGoal(Data, *Awareness);
	return EStateTreeRunStatus::Running;
}

EStateTreeRunStatus FStateTreeKochMoveToGoalTask::Tick(FStateTreeExecutionContext& Context, const float DeltaTime) const
{
	FInstanceDataType& Data = Context.GetInstanceData(*this);
	const UKochAwarenessComponent* Awareness = Data.Character ? Data.Character->GetAwareness() : nullptr;
	if (!Awareness || !Data.Controller)
	{
		return EStateTreeRunStatus::Failed;
	}
	Data.TimeSinceMove += DeltaTime;
	// Re-path on a new goal; retry every 2 s in case a move failed or got blocked.
	if (Awareness->GetGoalSerial() != Data.LastGoalSerial || Data.TimeSinceMove > 2.0f)
	{
		MoveToGoal(Data, *Awareness);
	}
	return EStateTreeRunStatus::Running;
}

void FStateTreeKochMoveToGoalTask::ExitState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const
{
	FInstanceDataType& Data = Context.GetInstanceData(*this);
	if (Data.Character)
	{
		Data.Character->SetMoveSpeedScale(1.0f);
	}
	if (Data.Controller)
	{
		Data.Controller->StopMovement();
		if (Data.bFaceTarget)
		{
			Data.Controller->ClearFocus(EAIFocusPriority::Gameplay);
		}
	}
}

#if WITH_EDITOR
FText FStateTreeKochMoveToGoalTask::GetDescription(const FGuid& ID, FStateTreeDataView InstanceDataView, const IStateTreeBindingLookup& BindingLookup, EStateTreeNodeFormatting Formatting /*= EStateTreeNodeFormatting::Text*/) const
{
	return FText::FromString("<b>Move To Awareness Goal</b>");
}
#endif

////////////////////////////////////////////////////////////////////
// Shoot burst

EStateTreeRunStatus FStateTreeKochShootBurstTask::EnterState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const
{
	FInstanceDataType& Data = Context.GetInstanceData(*this);
	ResolveTarget(Data.Target, Data.Character);
	if (!Data.Character || !Data.Target || !Data.Character->IsAlive())
	{
		return EStateTreeRunStatus::Failed;
	}
	Data.Elapsed = 0.0f;
	Data.bFiring = false;
	Data.bHasToken = false;
	return EStateTreeRunStatus::Running;
}

EStateTreeRunStatus FStateTreeKochShootBurstTask::Tick(FStateTreeExecutionContext& Context, const float DeltaTime) const
{
	FInstanceDataType& Data = Context.GetInstanceData(*this);
	if (!Data.Character || !Data.Target || !Data.Character->IsAlive())
	{
		return EStateTreeRunStatus::Failed;
	}

	Data.Elapsed += DeltaTime;
	const float ReactionTime = Data.Character->GetActiveTuning().ReactionTime;

	if (!Data.bFiring)
	{
		if (Data.Elapsed < ReactionTime)
		{
			return EStateTreeRunStatus::Running;
		}
		UKochSquadSubsystem* Squad = GetSquad(Data.Character);
		Data.bHasToken = !Squad || Squad->TryAcquireFireToken(Data.Character);
		if (!Data.bHasToken)
		{
			return EStateTreeRunStatus::Failed; // too many shooters right now: reposition instead
		}
		Data.Character->StartShooting(Data.Target);
		Data.bFiring = true;
		return EStateTreeRunStatus::Running;
	}

	const float Burst = Data.Character->GetBurstDuration() > 0.0f ? Data.Character->GetBurstDuration() : Data.BurstDuration;
	return (Data.Elapsed >= ReactionTime + Burst) ? EStateTreeRunStatus::Succeeded : EStateTreeRunStatus::Running;
}

void FStateTreeKochShootBurstTask::ExitState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const
{
	FInstanceDataType& Data = Context.GetInstanceData(*this);
	if (!Data.Character)
	{
		return;
	}
	if (Data.bFiring)
	{
		Data.Character->StopShooting();
		Data.bFiring = false;
	}
	if (Data.bHasToken)
	{
		if (UKochSquadSubsystem* Squad = GetSquad(Data.Character))
		{
			Squad->ReleaseFireToken(Data.Character);
		}
		Data.bHasToken = false;
	}
}

////////////////////////////////////////////////////////////////////
// CS peek

namespace
{
	EKochPeekKind PickPeekKind(const FStateTreeKochPeekInstanceData& Data, float DistToTarget, EKochDifficulty Difficulty)
	{
		if (Difficulty == EKochDifficulty::Easy)
		{
			return EKochPeekKind::WideSwing; // no baiting on Easy
		}
		if (Difficulty == EKochDifficulty::Hard && DistToTarget < Data.CrouchSprayRange && FMath::FRand() < 0.4f)
		{
			return EKochPeekKind::CrouchSpray;
		}
		const float Total = Data.JiggleWeight + Data.ShoulderWeight + Data.WideSwingWeight;
		if (Total <= KINDA_SMALL_NUMBER)
		{
			return EKochPeekKind::WideSwing;
		}
		const float Roll = FMath::FRand() * Total;
		if (Roll < Data.JiggleWeight)
		{
			return EKochPeekKind::Jiggle;
		}
		return (Roll < Data.JiggleWeight + Data.ShoulderWeight) ? EKochPeekKind::Shoulder : EKochPeekKind::WideSwing;
	}

	void SetStep(FStateTreeKochPeekInstanceData& Data, EKochPeekStep Step)
	{
		Data.Step = Step;
		Data.StepTime = 0.0f;
	}

	void EndBurst(FStateTreeKochPeekInstanceData& Data)
	{
		if (Data.bFiring)
		{
			Data.Character->StopShooting();
			Data.bFiring = false;
		}
		if (Data.bHasToken)
		{
			if (UKochSquadSubsystem* Squad = GetSquad(Data.Character))
			{
				Squad->ReleaseFireToken(Data.Character);
			}
			Data.bHasToken = false;
		}
	}

	void StartMoveBack(FStateTreeKochPeekInstanceData& Data)
	{
		Data.Controller->MoveToLocation(Data.Origin, ArriveTolerance * 0.5f, false, true, false, /*bCanStrafe*/ true);
		SetStep(Data, EKochPeekStep::MoveBack);
	}
}

EStateTreeRunStatus FStateTreeKochPeekTask::EnterState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const
{
	FInstanceDataType& Data = Context.GetInstanceData(*this);
	ResolveTarget(Data.Target, Data.Character);
	if (!Data.Character || !Data.Controller || !Data.Target || !Data.Character->IsAlive())
	{
		return EStateTreeRunStatus::Failed;
	}

	Data.bFiring = false;
	Data.bHasToken = false;
	Data.Origin = Data.Character->GetActorLocation();
	const FVector ToTarget = Data.Target->GetActorLocation() - Data.Origin;
	Data.Kind = PickPeekKind(Data, ToTarget.Size2D(), UKochDifficultySubsystem::GetCurrent(Data.Character));
	Data.Controller->SetFocus(Data.Target);

	if (Data.Kind == EKochPeekKind::CrouchSpray)
	{
		Data.Character->Crouch();
		Data.BurstDuration = Data.CrouchSprayBurst;
		SetStep(Data, EKochPeekStep::React);
		return EStateTreeRunStatus::Running;
	}

	// Strafe sideways relative to the target: CS peeks expose the body along the angle, not toward it.
	const float Sign = FMath::RandBool() ? 1.0f : -1.0f;
	const FVector Side = FVector::CrossProduct(ToTarget.GetSafeNormal2D(), FVector::UpVector) * Sign;
	const float Distance = (Data.Kind == EKochPeekKind::Jiggle) ? Data.JiggleDistance
		: (Data.Kind == EKochPeekKind::Shoulder) ? Data.ShoulderDistance
		: Data.WideSwingDistance;
	Data.OutPoint = ProjectToNav(Data.Character, Data.Origin + Side * Distance);
	Data.BurstDuration = Data.WideSwingBurst;

	Data.Controller->MoveToLocation(Data.OutPoint, ArriveTolerance * 0.5f, false, true, false, /*bCanStrafe*/ true);
	SetStep(Data, EKochPeekStep::MoveOut);
	return EStateTreeRunStatus::Running;
}

EStateTreeRunStatus FStateTreeKochPeekTask::Tick(FStateTreeExecutionContext& Context, const float DeltaTime) const
{
	FInstanceDataType& Data = Context.GetInstanceData(*this);
	if (!Data.Character || !Data.Controller || !Data.Target || !Data.Character->IsAlive())
	{
		return EStateTreeRunStatus::Failed;
	}

	Data.StepTime += DeltaTime;
	const FVector Here = Data.Character->GetActorLocation();

	switch (Data.Step)
	{
	case EKochPeekStep::MoveOut:
		if (FVector::Dist2D(Here, Data.OutPoint) <= ArriveTolerance || Data.StepTime > 1.0f)
		{
			Data.Controller->StopMovement(); // counter-strafe: braking tuned to reach accurate speed in ~80 ms
			SetStep(Data, EKochPeekStep::Stop);
		}
		break;

	case EKochPeekStep::Stop:
		if (IsAccurateSpeed(*Data.Character) || Data.StepTime >= Data.StopTimeout)
		{
			if (Data.Kind == EKochPeekKind::Jiggle || Data.Kind == EKochPeekKind::Shoulder)
			{
				StartMoveBack(Data);
			}
			else
			{
				SetStep(Data, EKochPeekStep::React);
			}
		}
		break;

	case EKochPeekStep::React:
		if (Data.StepTime >= Data.Character->GetActiveTuning().ReactionTime)
		{
			UKochSquadSubsystem* Squad = GetSquad(Data.Character);
			Data.bHasToken = !Squad || Squad->TryAcquireFireToken(Data.Character);
			if (!Data.bHasToken)
			{
				if (Data.Kind == EKochPeekKind::CrouchSpray)
				{
					Data.Character->UnCrouch();
					return EStateTreeRunStatus::Succeeded;
				}
				StartMoveBack(Data);
				break;
			}
			Data.Character->StartShooting(Data.Target);
			Data.bFiring = true;
			SetStep(Data, EKochPeekStep::Fire);
		}
		break;

	case EKochPeekStep::Fire:
		if (Data.StepTime >= Data.BurstDuration)
		{
			EndBurst(Data);
			if (Data.Kind == EKochPeekKind::CrouchSpray)
			{
				Data.Character->UnCrouch();
			}
			return EStateTreeRunStatus::Succeeded; // a wide swing stays committed on the new angle
		}
		break;

	case EKochPeekStep::MoveBack:
		if (FVector::Dist2D(Here, Data.Origin) <= ArriveTolerance || Data.StepTime > 0.8f)
		{
			return EStateTreeRunStatus::Succeeded;
		}
		break;
	}
	return EStateTreeRunStatus::Running;
}

void FStateTreeKochPeekTask::ExitState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const
{
	FInstanceDataType& Data = Context.GetInstanceData(*this);
	if (!Data.Character)
	{
		return;
	}
	EndBurst(Data);
	if (Data.Character->bIsCrouched)
	{
		Data.Character->UnCrouch();
	}
	if (Data.Controller)
	{
		if (Data.Step == EKochPeekStep::MoveOut || Data.Step == EKochPeekStep::MoveBack)
		{
			Data.Controller->StopMovement();
		}
		// Otherwise he keeps tracking the player's true position through walls after Engage ends.
		Data.Controller->ClearFocus(EAIFocusPriority::Gameplay);
	}
}
