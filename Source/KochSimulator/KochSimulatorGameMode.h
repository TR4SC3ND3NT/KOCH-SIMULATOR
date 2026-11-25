// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "KochSimulatorGameMode.generated.h"

/**
 *  Simple GameMode for a first person game.
 *  Spawns the player at the PlayerStart tagged PreferredStartTag (the prologue start on the street) when the level has
 *  one, instead of a random PlayerStart. A map URL portal (Map#Tag) still picks any other tagged start.
 */
UCLASS(abstract)
class AKochSimulatorGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AKochSimulatorGameMode();

protected:

	/** PlayerStartTag of the start used by default. None: engine default (first free start, random among several). */
	UPROPERTY(EditAnywhere, Category="Player Start")
	FName PreferredStartTag = FName("Prologue");

	virtual AActor* ChoosePlayerStart_Implementation(AController* Player) override;
};
