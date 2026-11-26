// See KochDifficultySubsystem.h.

#include "KochDifficultySubsystem.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

void UKochDifficultySubsystem::SetDifficulty(EKochDifficulty NewDifficulty)
{
	if (NewDifficulty == Difficulty)
	{
		return;
	}
	Difficulty = NewDifficulty;
	OnDifficultyChanged.Broadcast(Difficulty);
}

UKochDifficultySubsystem* UKochDifficultySubsystem::Get(const UObject* WorldContext)
{
	const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	const UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
	return GameInstance ? GameInstance->GetSubsystem<UKochDifficultySubsystem>() : nullptr;
}

EKochDifficulty UKochDifficultySubsystem::GetCurrent(const UObject* WorldContext)
{
	const UKochDifficultySubsystem* Subsystem = Get(WorldContext);
	return Subsystem ? Subsystem->GetDifficulty() : EKochDifficulty::Medium;
}
