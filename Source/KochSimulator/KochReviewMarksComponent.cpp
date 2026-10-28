#include "KochReviewMarksComponent.h"
#include "DrawDebugHelpers.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"

UKochReviewMarksComponent::UKochReviewMarksComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UKochReviewMarksComponent::BeginPlay()
{
	Super::BeginPlay();

	const APlayerController* PC = Cast<APlayerController>(GetOwner());
	if (PC && PC->IsLocalPlayerController())
	{
		Load();
	}
}

FString UKochReviewMarksComponent::FilePath()
{
	return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("QA"), TEXT("review_marks.json"));
}

void UKochReviewMarksComponent::AddMark()
{
	const APlayerController* PC = Cast<APlayerController>(GetOwner());
	if (!PC)
	{
		return;
	}
	FVector ViewLoc;
	FRotator ViewRot;
	PC->GetPlayerViewPoint(ViewLoc, ViewRot);
	FCollisionQueryParams Params(SCENE_QUERY_STAT(ReviewMark), true, PC->GetPawn());
	FHitResult Hit;
	if (!GetWorld()->LineTraceSingleByChannel(Hit, ViewLoc, ViewLoc + ViewRot.Vector() * TraceDistance, ECC_Visibility, Params))
	{
		return;
	}
	FString ActorName;
	if (const AActor* HitActor = Hit.GetActor())
	{
#if WITH_EDITOR
		ActorName = HitActor->GetActorLabel();
#else
		ActorName = HitActor->GetName();
#endif
	}
	Marks.Add({Hit.ImpactPoint, Hit.ImpactNormal, ActorName});
	Save();
	Redraw();
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(1, 3.0f, FColor::Red, FString::Printf(TEXT("Mark %d: %s"), Marks.Num(), *ActorName));
	}
}

void UKochReviewMarksComponent::RemoveLastMark()
{
	if (Marks.Num() == 0)
	{
		return;
	}
	Marks.Pop();
	Save();
	Redraw();
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(1, 3.0f, FColor::Yellow, FString::Printf(TEXT("Removed, %d marks left"), Marks.Num()));
	}
}

void UKochReviewMarksComponent::Save() const
{
	TArray<TSharedPtr<FJsonValue>> Items;
	for (const FReviewMark& Mark : Marks)
	{
		TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
		Obj->SetArrayField(TEXT("loc"), {MakeShared<FJsonValueNumber>(Mark.Location.X), MakeShared<FJsonValueNumber>(Mark.Location.Y),
										  MakeShared<FJsonValueNumber>(Mark.Location.Z)});
		Obj->SetArrayField(TEXT("normal"), {MakeShared<FJsonValueNumber>(Mark.Normal.X), MakeShared<FJsonValueNumber>(Mark.Normal.Y),
											 MakeShared<FJsonValueNumber>(Mark.Normal.Z)});
		Obj->SetStringField(TEXT("actor"), Mark.Actor);
		Items.Add(MakeShared<FJsonValueObject>(Obj));
	}
	FString Out;
	const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Out);
	FJsonSerializer::Serialize(Items, Writer);
	FFileHelper::SaveStringToFile(Out, *FilePath());
}

void UKochReviewMarksComponent::Load()
{
	FString In;
	if (!FFileHelper::LoadFileToString(In, *FilePath()))
	{
		return;
	}
	TArray<TSharedPtr<FJsonValue>> Items;
	if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(In), Items))
	{
		return;
	}
	Marks.Reset();
	for (const TSharedPtr<FJsonValue>& Item : Items)
	{
		const TSharedPtr<FJsonObject> Obj = Item->AsObject();
		const TArray<TSharedPtr<FJsonValue>>& L = Obj->GetArrayField(TEXT("loc"));
		const TArray<TSharedPtr<FJsonValue>>& N = Obj->GetArrayField(TEXT("normal"));
		Marks.Add({FVector(L[0]->AsNumber(), L[1]->AsNumber(), L[2]->AsNumber()),
				   FVector(N[0]->AsNumber(), N[1]->AsNumber(), N[2]->AsNumber()), Obj->GetStringField(TEXT("actor"))});
	}
	Redraw();
}

void UKochReviewMarksComponent::Redraw() const
{
	UWorld* World = GetWorld();
	FlushPersistentDebugLines(World);
	for (const FReviewMark& Mark : Marks)
	{
		// a dot on the surface plus a 1.5 m pole so it is visible from a distance
		DrawDebugSphere(World, Mark.Location, 12.0f, 12, FColor::Red, true, -1.0f, SDPG_Foreground, 2.0f);
		DrawDebugLine(World, Mark.Location, Mark.Location + FVector(0, 0, 150), FColor::Red, true, -1.0f, SDPG_World, 3.0f);
	}
}
