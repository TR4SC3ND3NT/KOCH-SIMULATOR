// Playtest aid (R4 -> everyone), owned by the player controllers: LMB drops a review mark where the crosshair hits,
// RMB removes the last one. Marks (location, normal, hit actor) are saved to Saved/QA/review_marks.json after every
// change and reloaded on start, so fixes can be made later in the editor. Drawn as persistent debug shapes
// (Development builds only).

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "KochReviewMarksComponent.generated.h"

UCLASS(ClassGroup=(Koch), meta=(BlueprintSpawnableComponent))
class KOCHSIMULATOR_API UKochReviewMarksComponent : public UActorComponent
{
	GENERATED_BODY()

public:

	UKochReviewMarksComponent();

	/** Trace from the owning controller's view and drop a mark on the first blocking hit. */
	void AddMark();

	/** Remove the most recent mark. */
	void RemoveLastMark();

protected:

	virtual void BeginPlay() override;

	/** Max distance of the mark trace (cm). */
	UPROPERTY(EditAnywhere, Category="Review")
	float TraceDistance = 5000.0f;

private:

	struct FReviewMark
	{
		FVector Location;
		FVector Normal;
		FString Actor;
	};
	TArray<FReviewMark> Marks;

	void Save() const;
	void Load();
	void Redraw() const;
	static FString FilePath();
};
