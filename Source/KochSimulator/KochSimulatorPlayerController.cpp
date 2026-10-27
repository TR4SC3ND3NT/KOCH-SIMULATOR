// Copyright Epic Games, Inc. All Rights Reserved.


#include "KochSimulatorPlayerController.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "InputMappingContext.h"
#include "KochSimulatorCameraManager.h"
#include "Blueprint/UserWidget.h"
#include "KochSimulator.h"
#include "Widgets/Input/SVirtualJoystick.h"
#include "DrawDebugHelpers.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"

AKochSimulatorPlayerController::AKochSimulatorPlayerController()
{
	// set the player camera manager class
	PlayerCameraManagerClass = AKochSimulatorCameraManager::StaticClass();
}

void AKochSimulatorPlayerController::BeginPlay()
{
	Super::BeginPlay();

	
	if (IsLocalPlayerController())
	{
		LoadReviewMarks();
	}

	// only spawn touch controls on local player controllers
	if (IsLocalPlayerController() && ShouldUseTouchControls())
	{
		// spawn the mobile controls widget
		MobileControlsWidget = CreateWidget<UUserWidget>(this, MobileControlsWidgetClass);

		if (MobileControlsWidget)
		{
			// add the controls to the player screen
			MobileControlsWidget->AddToPlayerScreen(0);

		} else {

			UE_LOG(LogKochSimulator, Error, TEXT("Could not spawn mobile controls widget."));

		}

	}
}

void AKochSimulatorPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();

	// only add IMCs for local player controllers
	if (IsLocalPlayerController())
	{
		// Add Input Mapping Context
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
		{
			for (UInputMappingContext* CurrentContext : DefaultMappingContexts)
			{
				Subsystem->AddMappingContext(CurrentContext, 0);
			}

			// only add these IMCs if we're not using mobile touch input
			if (!ShouldUseTouchControls())
			{
				for (UInputMappingContext* CurrentContext : MobileExcludedMappingContexts)
				{
					Subsystem->AddMappingContext(CurrentContext, 0);
				}
			}
		}

		// review marks: raw key bindings, independent of the Enhanced Input contexts
		InputComponent->BindKey(EKeys::LeftMouseButton, IE_Pressed, this, &AKochSimulatorPlayerController::AddReviewMark);
		InputComponent->BindKey(EKeys::RightMouseButton, IE_Pressed, this, &AKochSimulatorPlayerController::RemoveLastReviewMark);
	}

}

FString AKochSimulatorPlayerController::ReviewMarksPath() const
{
	return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("QA"), TEXT("review_marks.json"));
}

void AKochSimulatorPlayerController::AddReviewMark()
{
	FVector ViewLoc;
	FRotator ViewRot;
	GetPlayerViewPoint(ViewLoc, ViewRot);
	FCollisionQueryParams Params(SCENE_QUERY_STAT(ReviewMark), true, GetPawn());
	FHitResult Hit;
	if (!GetWorld()->LineTraceSingleByChannel(Hit, ViewLoc, ViewLoc + ViewRot.Vector() * ReviewTraceDistance, ECC_Visibility, Params))
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
	ReviewMarks.Add({Hit.ImpactPoint, Hit.ImpactNormal, ActorName});
	SaveReviewMarks();
	RedrawReviewMarks();
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(1, 3.0f, FColor::Red, FString::Printf(TEXT("Mark %d: %s"), ReviewMarks.Num(), *ActorName));
	}
}

void AKochSimulatorPlayerController::RemoveLastReviewMark()
{
	if (ReviewMarks.Num() == 0)
	{
		return;
	}
	ReviewMarks.Pop();
	SaveReviewMarks();
	RedrawReviewMarks();
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(1, 3.0f, FColor::Yellow, FString::Printf(TEXT("Removed, %d marks left"), ReviewMarks.Num()));
	}
}

void AKochSimulatorPlayerController::SaveReviewMarks() const
{
	TArray<TSharedPtr<FJsonValue>> Items;
	for (const FReviewMark& Mark : ReviewMarks)
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
	FFileHelper::SaveStringToFile(Out, *ReviewMarksPath());
}

void AKochSimulatorPlayerController::LoadReviewMarks()
{
	FString In;
	if (!FFileHelper::LoadFileToString(In, *ReviewMarksPath()))
	{
		return;
	}
	TArray<TSharedPtr<FJsonValue>> Items;
	if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(In), Items))
	{
		return;
	}
	ReviewMarks.Reset();
	for (const TSharedPtr<FJsonValue>& Item : Items)
	{
		const TSharedPtr<FJsonObject> Obj = Item->AsObject();
		const TArray<TSharedPtr<FJsonValue>>& L = Obj->GetArrayField(TEXT("loc"));
		const TArray<TSharedPtr<FJsonValue>>& N = Obj->GetArrayField(TEXT("normal"));
		ReviewMarks.Add({FVector(L[0]->AsNumber(), L[1]->AsNumber(), L[2]->AsNumber()),
						 FVector(N[0]->AsNumber(), N[1]->AsNumber(), N[2]->AsNumber()), Obj->GetStringField(TEXT("actor"))});
	}
	RedrawReviewMarks();
}

void AKochSimulatorPlayerController::RedrawReviewMarks() const
{
	UWorld* World = GetWorld();
	FlushPersistentDebugLines(World);
	for (const FReviewMark& Mark : ReviewMarks)
	{
		// a dot on the surface plus a 1.5 m pole so it is visible from a distance
		DrawDebugSphere(World, Mark.Location, 12.0f, 12, FColor::Red, true, -1.0f, SDPG_Foreground, 2.0f);
		DrawDebugLine(World, Mark.Location, Mark.Location + FVector(0, 0, 150), FColor::Red, true, -1.0f, SDPG_World, 3.0f);
	}
}

bool AKochSimulatorPlayerController::ShouldUseTouchControls() const
{
	// are we on a mobile platform? Should we force touch?
	return SVirtualJoystick::ShouldDisplayTouchInterface() || bForceTouchControls;
}
