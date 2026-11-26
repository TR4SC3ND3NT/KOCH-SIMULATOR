// Holds the game difficulty for the whole session (set by the menu, read by enemies and the squad subsystem).

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "KochEnemyTypes.h"
#include "KochDifficultySubsystem.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FKochDifficultyChanged, EKochDifficulty, NewDifficulty);

UCLASS()
class KOCHSIMULATOR_API UKochDifficultySubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category = "Koch|Difficulty")
	EKochDifficulty GetDifficulty() const { return Difficulty; }

	/** Applies immediately: living enemies re-tune, the squad restarts its phase schedule. */
	UFUNCTION(BlueprintCallable, Category = "Koch|Difficulty")
	void SetDifficulty(EKochDifficulty NewDifficulty);

	UPROPERTY(BlueprintAssignable, Category = "Koch|Difficulty")
	FKochDifficultyChanged OnDifficultyChanged;

	/** Medium if there is no game instance (editor previews, tests). */
	static EKochDifficulty GetCurrent(const UObject* WorldContext);
	static UKochDifficultySubsystem* Get(const UObject* WorldContext);

private:
	EKochDifficulty Difficulty = EKochDifficulty::Medium;
};
