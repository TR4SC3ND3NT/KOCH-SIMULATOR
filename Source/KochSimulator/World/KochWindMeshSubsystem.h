// Stops the CPU pose update of Dynamic Wind skeletal meshes (the PVE trees and shrubs) in game worlds.
// Why: their wind is computed on the GPU by the DynamicWind skinning transform provider from the skeleton's rest data;
// the CPU anim evaluation and the per-frame bone upload it triggers are never used, and cost ~28 ms of game thread
// with ~350 trees in view (2026-11-25 measurement, docs/decisions.md). The look and the wind motion are unchanged.
// Runs on BeginPlay and for every streamed-in World Partition cell. koch.WindMeshCPUPose 1 restores the engine default.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "KochWindMeshSubsystem.generated.h"

class ULevel;

UCLASS()
class KOCHSIMULATOR_API UKochWindMeshSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:

	virtual void OnWorldBeginPlay(UWorld& InWorld) override;
	virtual void Deinitialize() override;

	/** Meshes whose CPU pose update was stopped so far. */
	int32 GetNumStopped() const { return NumStopped; }

protected:

	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;

private:

	void OnLevelAdded(ULevel* Level, UWorld* World);

	void ProcessLevel(ULevel* Level);

	FDelegateHandle LevelAddedHandle;

	int32 NumStopped = 0;
};
