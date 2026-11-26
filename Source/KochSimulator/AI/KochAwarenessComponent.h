// Per-enemy awareness: what the enemy knows about the player (sight, hearing, squad callouts, memory),
// its state (Unaware/Suspicious/Hunt/Engage/Search) and where it wants to stand. Lives on AKochEnemyCharacter;
// Koch StateTree nodes read it. Runs on a 0.1 s timer, no Tick. Spec: docs/design/enemies.md §3a

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Perception/AIPerceptionTypes.h"
#include "KochEnemyTypes.h"
#include "KochAwarenessComponent.generated.h"

class AAIController;
class AKochEnemyCharacter;
class UAIPerceptionComponent;

UCLASS(ClassGroup = (Koch), meta = (BlueprintSpawnableComponent))
class KOCHSIMULATOR_API UKochAwarenessComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UKochAwarenessComponent();

	UFUNCTION(BlueprintPure, Category = "Koch|Awareness")
	EKochAwareness GetState() const { return State; }

	/** The player this enemy knows about (may be out of sight). */
	UFUNCTION(BlueprintPure, Category = "Koch|Awareness")
	AActor* GetTarget() const { return Target.Get(); }

	UFUNCTION(BlueprintPure, Category = "Koch|Awareness")
	bool HasLineOfSight() const { return bInSight; }

	FVector GetLastKnownLocation() const { return LastKnownLocation; }

	/** Seconds since the player was last seen or reported. */
	float GetKnowledgeAge() const;

	/** Where the enemy wants to be now; bumps GetGoalSerial() when it changes meaningfully. */
	FVector GetMoveGoal() const { return MoveGoal; }
	uint32 GetGoalSerial() const { return GoalSerial; }

	/** Hooks the controller's AIPerception (configures sight + hearing from the active tuning). */
	void BindToController(AAIController* Controller);
	void Unbind();

	/** Re-applies perception ranges after a difficulty change. */
	void ApplyPerceptionTuning();

	/** Squad radio: another enemy saw the player. */
	void ReceiveCallout(AActor* InTarget, const FVector& Location, const FVector& Velocity, double TimeSeen);

	/** Only actors with this tag are hunted. */
	UPROPERTY(EditAnywhere, Category = "Koch|Awareness")
	FName TargetTag = FName("Player");

	/** Awareness update period (timer, not Tick). Footsteps arrive as hearing stimuli tagged "Footstep". */
	UPROPERTY(EditAnywhere, Category = "Koch|Awareness", meta = (ClampMin = 0.05, Units = "s"))
	float ThinkInterval = 0.1f;

	UPROPERTY(EditAnywhere, Category = "Koch|Awareness", meta = (ClampMin = 0, Units = "s"))
	float SuspiciousTime = 6.0f;

	UPROPERTY(EditAnywhere, Category = "Koch|Awareness", meta = (ClampMin = 0, Units = "cm"))
	float SearchRadius = 900.0f;

	UPROPERTY(EditAnywhere, Category = "Koch|Awareness", meta = (ClampMin = 1, ClampMax = 8))
	int32 SearchPointCount = 4;

	/** Re-evaluate the fighting position this often while engaged. */
	UPROPERTY(EditAnywhere, Category = "Koch|Awareness", meta = (ClampMin = 0.2, Units = "s"))
	float EngagePositionInterval = 1.0f;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	UFUNCTION()
	void HandlePerceptionUpdated(AActor* Actor, FAIStimulus Stimulus);

	void Think();
	void SetState(EKochAwareness NewState);
	void UpdateGoal(double Now);
	void SetGoal(const FVector& NewGoal, bool bForce = false);
	void BuildSearchPoints();
	bool FindEngagePosition(const AActor& InTarget, FVector& OutLocation) const;
	FKochTargetBelief MakeBelief(double Now) const;
	AKochEnemyCharacter* GetEnemy() const;

	TWeakObjectPtr<UAIPerceptionComponent> Perception;
	TWeakObjectPtr<AActor> Target;

	EKochAwareness State = EKochAwareness::Unaware;
	double StateEnterTime = 0.0;

	FVector LastKnownLocation = FVector::ZeroVector;
	FVector LastKnownVelocity = FVector::ZeroVector;
	double LastSeenTime = -1.0e9;
	double LastCalloutTime = -1.0e9;
	bool bInSight = false;
	/** Accumulated "I see something" seconds; noticing needs NoticeTime. */
	float Exposure = 0.0f;

	FVector NoiseLocation = FVector::ZeroVector;
	TArray<FVector> SearchPoints;

	FVector MoveGoal = FVector::ZeroVector;
	uint32 GoalSerial = 0;
	double NextEngageEvalTime = 0.0;

	FTimerHandle ThinkTimer;
};
