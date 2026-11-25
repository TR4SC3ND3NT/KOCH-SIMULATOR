// Copyright Epic Games, Inc. All Rights Reserved.

#include "KochSimulatorGameMode.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerStart.h"

AKochSimulatorGameMode::AKochSimulatorGameMode()
{
	// stub
}

AActor* AKochSimulatorGameMode::ChoosePlayerStart_Implementation(AController* Player)
{
	if (!PreferredStartTag.IsNone())
	{
		for (TActorIterator<APlayerStart> It(GetWorld()); It; ++It)
		{
			if (It->PlayerStartTag == PreferredStartTag)
			{
				return *It;
			}
		}
	}

	return Super::ChoosePlayerStart_Implementation(Player);
}
