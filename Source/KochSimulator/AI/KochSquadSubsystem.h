// Squad brain for hostile NPCs: Pac-Man Regroup/Chase phase timer, role move targets, Cruise-Elroy speed-up, fire tokens.
// Enemies (AKochEnemyCharacter) register here; Koch StateTree tasks query it. Spec: docs/design/enemies.md

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "KochEnemyTypes.h"
#include "KochSquadSubsystem.generated.h"

class AKochEnemyCharacter;

UCLASS()
class KOCHSIMULATOR_API UKochSquadSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	void RegisterEnemy(AKochEnemyCharacter* Enemy);
	void UnregisterEnemy(AKochEnemyCharacter* Enemy);

	UFUNCTION(BlueprintPure, Category = "Koch|Squad")
	EKochSquadPhase GetPhase() const { return Phase; }

	/** Increments on every phase switch; tasks re-path when it changes (Pac-Man ghosts reverse on a switch). */
	uint32 GetPhaseSerial() const { return PhaseSerial; }

	UFUNCTION(BlueprintPure, Category = "Koch|Squad")
	int32 GetAliveCount() const;

	/** True when few enemies are left: Chaser/Peeker ignore Regroup and run faster. */
	UFUNCTION(BlueprintPure, Category = "Koch|Squad")
	bool IsElroyActive() const { return bElroy; }

	/**
	 * Role target for Enemy around what it BELIEVES about the player (last known position), projected to the navmesh.
	 * False = no navmesh hit (OutLocation is the raw point).
	 */
	bool ComputeMoveTarget(const AKochEnemyCharacter& Enemy, const FKochTargetBelief& Belief, FVector& OutLocation) const;

	/** Squad radio: Reporter saw Target; the others hear it after the difficulty's callout delay. */
	void ReportSighting(const AKochEnemyCharacter* Reporter, AActor* Target, const FVector& Location, const FVector& Velocity, double TimeSeen);

	/** True if another living enemy wants to stand within Radius of Location (spreads fighting positions). */
	bool IsSpotTaken(const FVector& Location, const AKochEnemyCharacter* Exclude, float Radius) const;

	/** Limits how many enemies shoot at once (2/3/4 by difficulty). Holding a token twice is fine. */
	bool TryAcquireFireToken(const AKochEnemyCharacter* Enemy);
	void ReleaseFireToken(const AKochEnemyCharacter* Enemy);

	FKochRoleTargetParams TargetParams;

	/** Player speed / MaxWalkSpeed above which footsteps are audible. */
	float FootstepSpeedRatio = 0.6f;
	/** Footstep audible range (cm); each enemy's HearingRange also applies. */
	float FootstepRange = 1500.0f;

protected:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;
	virtual void Deinitialize() override;

private:
	void RestartSchedule();
	void AdvancePhase();
	void SetPhase(EKochSquadPhase NewPhase);
	void UpdateElroy();
	const AKochEnemyCharacter* FindLeaderFor(const AKochEnemyCharacter& Enemy) const;

	UFUNCTION()
	void HandleDifficultyChanged(EKochDifficulty NewDifficulty);

	UFUNCTION()
	void HandleEnemyDied();

	/** Turns the player's running into hearing stimuli (CS rule: walking and crouching are silent). */
	void EmitPlayerFootsteps();
	FTimerHandle FootstepTimer;

	TArray<TWeakObjectPtr<AKochEnemyCharacter>> Enemies;
	TArray<TWeakObjectPtr<const AKochEnemyCharacter>> FireTokenHolders;

	FTimerHandle PhaseTimer;
	int32 PhaseStep = 0;
	uint32 PhaseSerial = 0;
	EKochSquadPhase Phase = EKochSquadPhase::Regroup;
	EKochDifficulty Difficulty = EKochDifficulty::Medium;
	bool bElroy = false;
};
