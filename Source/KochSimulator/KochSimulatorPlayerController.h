// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "KochSimulatorPlayerController.generated.h"

class UInputMappingContext;
class UUserWidget;

/**
 *  Simple first person Player Controller
 *  Manages the input mapping context.
 *  Overrides the Player Camera Manager class.
 */
UCLASS(abstract, config="Game")
class KOCHSIMULATOR_API AKochSimulatorPlayerController : public APlayerController
{
	GENERATED_BODY()
	
public:

	/** Constructor */
	AKochSimulatorPlayerController();

protected:

	/** Input Mapping Contexts */
	UPROPERTY(EditAnywhere, Category="Input|Input Mappings")
	TArray<UInputMappingContext*> DefaultMappingContexts;

	/** Input Mapping Contexts */
	UPROPERTY(EditAnywhere, Category="Input|Input Mappings")
	TArray<UInputMappingContext*> MobileExcludedMappingContexts;

	/** Mobile controls widget to spawn */
	UPROPERTY(EditAnywhere, Category="Input|Touch Controls")
	TSubclassOf<UUserWidget> MobileControlsWidgetClass;

	/** Pointer to the mobile controls widget */
	UPROPERTY()
	TObjectPtr<UUserWidget> MobileControlsWidget;

	/** If true, the player will use UMG touch controls even if not playing on mobile platforms */
	UPROPERTY(EditAnywhere, Config, Category = "Input|Touch Controls")
	bool bForceTouchControls = false;

	/** Gameplay initialization */
	virtual void BeginPlay() override;

	/** Input mapping context setup */
	virtual void SetupInputComponent() override;

	/** Returns true if the player should use UMG touch controls */
	bool ShouldUseTouchControls() const;

	// --- Review marks (playtest aid): LMB drops a mark where the crosshair hits, RMB removes the last one. Marks are
	// saved to Saved/QA/review_marks.json (location, normal, hit actor) after every change and reloaded on start, so
	// fixes can be made later in the editor. Drawn as persistent debug shapes (Development builds only).

	/** Max distance of the mark trace (cm). */
	UPROPERTY(EditAnywhere, Category="Review")
	float ReviewTraceDistance = 5000.0f;

	struct FReviewMark
	{
		FVector Location;
		FVector Normal;
		FString Actor;
	};
	TArray<FReviewMark> ReviewMarks;

	void AddReviewMark();
	void RemoveLastReviewMark();
	void SaveReviewMarks() const;
	void LoadReviewMarks();
	void RedrawReviewMarks() const;
	FString ReviewMarksPath() const;
};
