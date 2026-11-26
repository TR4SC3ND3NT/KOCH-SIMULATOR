// CS-style kill feed (top right): "Killer [weapon icon] [headshot] Victim", newest at the bottom, fades out.
// Built in C++ (no designer tree needed); WBP_KochKillFeed only sets the icon. Created by AShooterPlayerController.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "KochKillFeedSubsystem.h"
#include "KochKillFeedWidget.generated.h"

class UVerticalBox;
class UBorder;
class UTexture2D;

UCLASS()
class KOCHSIMULATOR_API UKochKillFeedWidget : public UUserWidget
{
	GENERATED_BODY()

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

	UFUNCTION()
	void HandleKill(const FKochKillInfo& Kill);

	/** Shown after the weapon icon on headshot kills. */
	UPROPERTY(EditDefaultsOnly, Category = "Koch|KillFeed")
	TObjectPtr<UTexture2D> HeadshotIcon;

	UPROPERTY(EditDefaultsOnly, Category = "Koch|KillFeed", meta = (ClampMin = 1, ClampMax = 12))
	int32 MaxRows = 5;

	/** Seconds a line stays, including the fade. */
	UPROPERTY(EditDefaultsOnly, Category = "Koch|KillFeed", meta = (ClampMin = 1, Units = "s"))
	float LineLifetime = 7.0f;

	UPROPERTY(EditDefaultsOnly, Category = "Koch|KillFeed", meta = (ClampMin = 0, Units = "s"))
	float FadeTime = 0.6f;

	/** Icon height in slate units; width follows the texture aspect. */
	UPROPERTY(EditDefaultsOnly, Category = "Koch|KillFeed", meta = (ClampMin = 8))
	float IconHeight = 22.0f;

	UPROPERTY(EditDefaultsOnly, Category = "Koch|KillFeed", meta = (ClampMin = 8))
	int32 FontSize = 13;

	/** Distance from the top-right corner of the screen. */
	UPROPERTY(EditDefaultsOnly, Category = "Koch|KillFeed")
	FVector2D ScreenOffset = FVector2D(24.0, 24.0);

	UPROPERTY(EditDefaultsOnly, Category = "Koch|KillFeed")
	FLinearColor FriendlyColor = FLinearColor(0.36f, 0.66f, 1.0f);

	UPROPERTY(EditDefaultsOnly, Category = "Koch|KillFeed")
	FLinearColor HostileColor = FLinearColor(0.92f, 0.75f, 0.29f);

	/** Outline of lines the player is part of (CS marks your own kills and deaths in red). */
	UPROPERTY(EditDefaultsOnly, Category = "Koch|KillFeed")
	FLinearColor PlayerLineOutline = FLinearColor(0.85f, 0.12f, 0.1f);

private:
	struct FLine
	{
		TObjectPtr<UBorder> Widget;
		double SpawnTime = 0.0;
	};

	void AddIcon(class UHorizontalBox* Box, UTexture2D* Texture);
	void UpdateLines();

	UPROPERTY()
	TObjectPtr<UVerticalBox> LinesBox;

	TArray<FLine> Lines;
	FTimerHandle FadeTimer;
};
