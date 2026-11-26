// StateTree nodes for KOCH enemies: awareness-state condition, move to the awareness goal (role target around the
// last known position, fighting spot, search point), shoot with reaction time + fire token, Donk's CS-style peeks. Used in the enemy StateTree asset (Content/KochSimulator/AI). Spec: docs/design/enemies.md

#pragma once

#include "CoreMinimal.h"
#include "StateTreeTaskBase.h"
#include "StateTreeConditionBase.h"
#include "KochEnemyTypes.h"
#include "KochStateTreeTasks.generated.h"

class AAIController;
class AKochEnemyCharacter;

////////////////////////////////////////////////////////////////////
// Awareness condition

USTRUCT()
struct FStateTreeKochAwarenessConditionInstanceData
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, Category = Context)
	TObjectPtr<AKochEnemyCharacter> Character;

	UPROPERTY(EditAnywhere, Category = Parameter)
	EKochAwareness State = EKochAwareness::Engage;
};

/** Passes when the enemy's awareness state equals State (use Invert in the editor for "not"). */
USTRUCT(DisplayName = "Koch Awareness Is", Category = "Koch")
struct FStateTreeKochAwarenessCondition : public FStateTreeConditionCommonBase
{
	GENERATED_BODY()

	using FInstanceDataType = FStateTreeKochAwarenessConditionInstanceData;
	virtual const UStruct* GetInstanceDataType() const override { return FInstanceDataType::StaticStruct(); }

	virtual bool TestCondition(FStateTreeExecutionContext& Context) const override;

#if WITH_EDITOR
	virtual FText GetDescription(const FGuid& ID, FStateTreeDataView InstanceDataView, const IStateTreeBindingLookup& BindingLookup, EStateTreeNodeFormatting Formatting = EStateTreeNodeFormatting::Text) const override;
#endif
};

////////////////////////////////////////////////////////////////////
// Move to awareness goal

USTRUCT()
struct FStateTreeKochMoveToGoalInstanceData
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, Category = Context)
	TObjectPtr<AKochEnemyCharacter> Character;

	UPROPERTY(EditAnywhere, Category = Context)
	TObjectPtr<AAIController> Controller;

	/** 1 = run; < 1 walks (CS: walking is silent). Suspicious/Search ~0.45. */
	UPROPERTY(EditAnywhere, Category = Parameter, meta = (ClampMin = 0.1, ClampMax = 1))
	float SpeedScale = 1.0f;

	UPROPERTY(EditAnywhere, Category = Parameter, meta = (ClampMin = 0, Units = "cm"))
	float AcceptanceRadius = 60.0f;

	/** Keep looking at the known target while moving (strafe), e.g. in Engage. */
	UPROPERTY(EditAnywhere, Category = Parameter)
	bool bFaceTarget = false;

	uint32 LastGoalSerial = 0;
	float TimeSinceMove = 0.0f;
};

/** Follows UKochAwarenessComponent::GetMoveGoal (anchor / noise / role target / fighting spot / search point). Runs until the state exits. */
USTRUCT(meta = (DisplayName = "Koch Move To Awareness Goal", Category = "Koch"))
struct FStateTreeKochMoveToGoalTask : public FStateTreeTaskCommonBase
{
	GENERATED_BODY()

	using FInstanceDataType = FStateTreeKochMoveToGoalInstanceData;
	virtual const UStruct* GetInstanceDataType() const override { return FInstanceDataType::StaticStruct(); }

	virtual EStateTreeRunStatus EnterState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const override;
	virtual EStateTreeRunStatus Tick(FStateTreeExecutionContext& Context, const float DeltaTime) const override;
	virtual void ExitState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const override;

#if WITH_EDITOR
	virtual FText GetDescription(const FGuid& ID, FStateTreeDataView InstanceDataView, const IStateTreeBindingLookup& BindingLookup, EStateTreeNodeFormatting Formatting = EStateTreeNodeFormatting::Text) const override;
#endif
};

////////////////////////////////////////////////////////////////////
// Shoot burst (reaction time + fire token)

USTRUCT()
struct FStateTreeKochShootBurstInstanceData
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, Category = Context)
	TObjectPtr<AKochEnemyCharacter> Character;

	/** Optional; unbound = the target the enemy's awareness knows about. */
	UPROPERTY(EditAnywhere, Category = Input, meta = (Optional))
	TObjectPtr<AActor> Target;

	/** Burst length (s); 0.3 s = 3 AK rounds at 600 RPM. */
	UPROPERTY(EditAnywhere, Category = Parameter, meta = (ClampMin = 0.05, Units = "s"))
	float BurstDuration = 0.3f;

	float Elapsed = 0.0f;
	bool bFiring = false;
	bool bHasToken = false;
};

/** Waits the enemy's reaction time, takes a squad fire token, fires one burst. Fails if no token is free. */
USTRUCT(meta = (DisplayName = "Koch Shoot Burst", Category = "Koch"))
struct FStateTreeKochShootBurstTask : public FStateTreeTaskCommonBase
{
	GENERATED_BODY()

	using FInstanceDataType = FStateTreeKochShootBurstInstanceData;
	virtual const UStruct* GetInstanceDataType() const override { return FInstanceDataType::StaticStruct(); }

	virtual EStateTreeRunStatus EnterState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const override;
	virtual EStateTreeRunStatus Tick(FStateTreeExecutionContext& Context, const float DeltaTime) const override;
	virtual void ExitState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const override;
};

////////////////////////////////////////////////////////////////////
// CS-style peek (Donk)

UENUM()
enum class EKochPeekKind : uint8
{
	Jiggle,      // out and back, no shot: baits the player
	Shoulder,    // tiny exposure, no shot
	WideSwing,   // commit past the angle, counter-strafe, burst
	CrouchSpray  // close range: crouch and spray
};

UENUM()
enum class EKochPeekStep : uint8
{
	MoveOut,
	Stop,
	React,
	Fire,
	MoveBack
};

USTRUCT()
struct FStateTreeKochPeekInstanceData
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, Category = Context)
	TObjectPtr<AKochEnemyCharacter> Character;

	UPROPERTY(EditAnywhere, Category = Context)
	TObjectPtr<AAIController> Controller;

	/** Optional; unbound = the target the enemy's awareness knows about. */
	UPROPERTY(EditAnywhere, Category = Input, meta = (Optional))
	TObjectPtr<AActor> Target;

	/** Chance weights for the peek kinds (normalised at runtime). */
	UPROPERTY(EditAnywhere, Category = Parameter, meta = (ClampMin = 0))
	float JiggleWeight = 0.3f;

	UPROPERTY(EditAnywhere, Category = Parameter, meta = (ClampMin = 0))
	float ShoulderWeight = 0.15f;

	UPROPERTY(EditAnywhere, Category = Parameter, meta = (ClampMin = 0))
	float WideSwingWeight = 0.55f;

	UPROPERTY(EditAnywhere, Category = Parameter, meta = (ClampMin = 0, Units = "cm"))
	float JiggleDistance = 70.0f;

	UPROPERTY(EditAnywhere, Category = Parameter, meta = (ClampMin = 0, Units = "cm"))
	float ShoulderDistance = 35.0f;

	UPROPERTY(EditAnywhere, Category = Parameter, meta = (ClampMin = 0, Units = "cm"))
	float WideSwingDistance = 220.0f;

	/** Inside this range a Hard-difficulty peeker may crouch-spray instead of swinging. */
	UPROPERTY(EditAnywhere, Category = Parameter, meta = (ClampMin = 0, Units = "cm"))
	float CrouchSprayRange = 1000.0f;

	UPROPERTY(EditAnywhere, Category = Parameter, meta = (ClampMin = 0.05, Units = "s"))
	float WideSwingBurst = 0.3f;

	UPROPERTY(EditAnywhere, Category = Parameter, meta = (ClampMin = 0.05, Units = "s"))
	float CrouchSprayBurst = 0.8f;

	/** Max wait for the counter-strafe stop before shooting anyway (CS2 ~80 ms). */
	UPROPERTY(EditAnywhere, Category = Parameter, meta = (ClampMin = 0, Units = "s"))
	float StopTimeout = 0.12f;

	EKochPeekKind Kind = EKochPeekKind::WideSwing;
	EKochPeekStep Step = EKochPeekStep::MoveOut;
	FVector Origin = FVector::ZeroVector;
	FVector OutPoint = FVector::ZeroVector;
	float StepTime = 0.0f;
	float BurstDuration = 0.0f;
	bool bHasToken = false;
	bool bFiring = false;
};

/** One CS-style peek: jiggle, shoulder, wide swing (stop -> react -> burst) or crouch-spray. Succeeds when done. */
USTRUCT(meta = (DisplayName = "Koch CS Peek", Category = "Koch"))
struct FStateTreeKochPeekTask : public FStateTreeTaskCommonBase
{
	GENERATED_BODY()

	using FInstanceDataType = FStateTreeKochPeekInstanceData;
	virtual const UStruct* GetInstanceDataType() const override { return FInstanceDataType::StaticStruct(); }

	virtual EStateTreeRunStatus EnterState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const override;
	virtual EStateTreeRunStatus Tick(FStateTreeExecutionContext& Context, const float DeltaTime) const override;
	virtual void ExitState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const override;
};
