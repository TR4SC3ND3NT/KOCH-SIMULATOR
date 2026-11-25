// See KochWindMeshSubsystem.h.

#include "World/KochWindMeshSubsystem.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/AssetUserData.h"
#include "Engine/Level.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "HAL/IConsoleManager.h"

namespace
{
	TAutoConsoleVariable<bool> CVarWindMeshCPUPose(
		TEXT("koch.WindMeshCPUPose"),
		false,
		TEXT("true: Dynamic Wind skeletal meshes keep their CPU pose update (engine default, costs game-thread time). ")
		TEXT("false: it is stopped when they load; the GPU wind is unaffected. Takes effect for meshes loaded afterwards."),
		ECVF_Default);

	/** Matched by class name so the game module does not link the experimental DynamicWind plugin. */
	const FName DynamicWindDataClass(TEXT("DynamicWindSkeletalData"));

	bool HasDynamicWind(const USkeletalMeshComponent& Component)
	{
		const USkeletalMesh* Mesh = Component.GetSkeletalMeshAsset();
		const TArray<UAssetUserData*>* UserData = Mesh ? Mesh->GetAssetUserDataArray() : nullptr;
		if (!UserData)
		{
			return false;
		}

		for (const UAssetUserData* Data : *UserData)
		{
			if (Data && Data->GetClass()->GetFName() == DynamicWindDataClass)
			{
				return true;
			}
		}
		return false;
	}
}

bool UKochWindMeshSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

void UKochWindMeshSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);

	// World Partition streams cells in as levels; catch every one after this point
	LevelAddedHandle = FWorldDelegates::LevelAddedToWorld.AddUObject(this, &UKochWindMeshSubsystem::OnLevelAdded);

	for (ULevel* Level : InWorld.GetLevels())
	{
		ProcessLevel(Level);
	}
}

void UKochWindMeshSubsystem::Deinitialize()
{
	FWorldDelegates::LevelAddedToWorld.Remove(LevelAddedHandle);

	Super::Deinitialize();
}

void UKochWindMeshSubsystem::OnLevelAdded(ULevel* Level, UWorld* World)
{
	if (World == GetWorld())
	{
		ProcessLevel(Level);
	}
}

void UKochWindMeshSubsystem::ProcessLevel(ULevel* Level)
{
	if (!Level || CVarWindMeshCPUPose.GetValueOnGameThread())
	{
		return;
	}

	TArray<USkeletalMeshComponent*> Components;
	for (AActor* Actor : Level->Actors)
	{
		if (!Actor)
		{
			continue;
		}

		Components.Reset();
		Actor->GetComponents(Components);
		for (USkeletalMeshComponent* Component : Components)
		{
			if (Component->PrimaryComponentTick.bStartWithTickEnabled && HasDynamicWind(*Component))
			{
				// no tick: no CPU evaluation and no per-frame bone upload; the pose stays the one computed on register.
				// Levels can arrive before their actors' BeginPlay, which re-enables ticking unless bStartWithTickEnabled
				// is cleared too (UActorComponent::SetupActorComponentTickFunction).
				Component->PrimaryComponentTick.bStartWithTickEnabled = false;
				Component->SetComponentTickEnabled(false);
				++NumStopped;
			}
		}
	}
}
