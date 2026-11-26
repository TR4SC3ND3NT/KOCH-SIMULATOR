// See KochKillFeedWidget.h.

#include "KochKillFeedWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Styling/CoreStyle.h"
#include "TimerManager.h"

namespace
{
	constexpr float FadeTickInterval = 0.1f; // s; only runs while lines are shown
}

void UKochKillFeedWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	// Full-screen canvas with an auto-sized column pinned to the top-right corner.
	UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>();
	WidgetTree->RootWidget = Canvas;
	LinesBox = WidgetTree->ConstructWidget<UVerticalBox>();
	UCanvasPanelSlot* BoxSlot = Canvas->AddChildToCanvas(LinesBox);
	BoxSlot->SetAnchors(FAnchors(1.0f, 0.0f));
	BoxSlot->SetAlignment(FVector2D(1.0, 0.0));
	BoxSlot->SetPosition(FVector2D(-ScreenOffset.X, ScreenOffset.Y));
	BoxSlot->SetAutoSize(true);
	SetVisibility(ESlateVisibility::HitTestInvisible);
}

void UKochKillFeedWidget::NativeConstruct()
{
	Super::NativeConstruct();
	if (UKochKillFeedSubsystem* Subsystem = GetWorld() ? GetWorld()->GetSubsystem<UKochKillFeedSubsystem>() : nullptr)
	{
		Subsystem->OnKill.AddUniqueDynamic(this, &UKochKillFeedWidget::HandleKill);
	}
}

void UKochKillFeedWidget::NativeDestruct()
{
	if (UWorld* World = GetWorld())
	{
		if (UKochKillFeedSubsystem* Subsystem = World->GetSubsystem<UKochKillFeedSubsystem>())
		{
			Subsystem->OnKill.RemoveDynamic(this, &UKochKillFeedWidget::HandleKill);
		}
		World->GetTimerManager().ClearTimer(FadeTimer);
	}
	Super::NativeDestruct();
}

void UKochKillFeedWidget::HandleKill(const FKochKillInfo& Kill)
{
	UWorld* World = GetWorld();
	if (!World || !LinesBox)
	{
		return;
	}

	const FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle("Bold", FontSize);
	auto AddName = [this, &Font](UHorizontalBox* Box, const FText& Name, bool bPlayer)
	{
		UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>();
		Text->SetText(Name);
		Text->SetFont(Font);
		Text->SetColorAndOpacity(FSlateColor(bPlayer ? FriendlyColor : HostileColor));
		Text->SetShadowOffset(FVector2D(1.0, 1.0));
		Text->SetShadowColorAndOpacity(FLinearColor(0.0f, 0.0f, 0.0f, 0.8f));
		UHorizontalBoxSlot* TextSlot = Box->AddChildToHorizontalBox(Text);
		TextSlot->SetVerticalAlignment(VAlign_Center);
		TextSlot->SetPadding(FMargin(4.0f, 0.0f));
	};

	UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
	if (!Kill.KillerName.IsEmpty())
	{
		AddName(Row, Kill.KillerName, Kill.bKillerIsPlayer);
	}
	AddIcon(Row, Kill.WeaponIcon);
	if (Kill.bHeadshot)
	{
		AddIcon(Row, HeadshotIcon);
	}
	AddName(Row, Kill.VictimName, Kill.bVictimIsPlayer);

	// Dark rounded plate; red outline when the player killed or died (CS).
	FSlateBrush Plate;
	Plate.DrawAs = ESlateBrushDrawType::RoundedBox;
	Plate.TintColor = FSlateColor(FLinearColor(0.0f, 0.0f, 0.0f, 0.55f));
	const bool bPlayerLine = Kill.bKillerIsPlayer || Kill.bVictimIsPlayer;
	Plate.OutlineSettings = FSlateBrushOutlineSettings(3.0f, FSlateColor(bPlayerLine ? PlayerLineOutline : FLinearColor::Transparent), bPlayerLine ? 1.5f : 0.0f);

	UBorder* Line = WidgetTree->ConstructWidget<UBorder>();
	Line->SetBrush(Plate);
	Line->SetPadding(FMargin(6.0f, 3.0f));
	Line->SetContent(Row);
	UVerticalBoxSlot* LineSlot = LinesBox->AddChildToVerticalBox(Line);
	LineSlot->SetHorizontalAlignment(HAlign_Right);
	LineSlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 3.0f));

	Lines.Add({ Line, World->GetTimeSeconds() });
	while (Lines.Num() > MaxRows)
	{
		Lines[0].Widget->RemoveFromParent();
		Lines.RemoveAt(0);
	}
	if (!World->GetTimerManager().IsTimerActive(FadeTimer))
	{
		World->GetTimerManager().SetTimer(FadeTimer, this, &UKochKillFeedWidget::UpdateLines, FadeTickInterval, true);
	}
}

void UKochKillFeedWidget::AddIcon(UHorizontalBox* Box, UTexture2D* Texture)
{
	if (!Texture)
	{
		return;
	}
	const float Aspect = Texture->GetSizeY() > 0 ? float(Texture->GetSizeX()) / float(Texture->GetSizeY()) : 1.0f;
	UImage* Icon = WidgetTree->ConstructWidget<UImage>();
	FSlateBrush Brush; // ImageSize = desired size, so the silhouette keeps its aspect
	Brush.SetResourceObject(Texture);
	Brush.ImageSize = FVector2D(IconHeight * Aspect, IconHeight);
	Icon->SetBrush(Brush);
	UHorizontalBoxSlot* IconSlot = Box->AddChildToHorizontalBox(Icon);
	IconSlot->SetVerticalAlignment(VAlign_Center);
	IconSlot->SetPadding(FMargin(4.0f, 0.0f));
}

void UKochKillFeedWidget::UpdateLines()
{
	const UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	const double Now = World->GetTimeSeconds();
	for (int32 Index = Lines.Num() - 1; Index >= 0; --Index)
	{
		const double Age = Now - Lines[Index].SpawnTime;
		if (Age >= LineLifetime)
		{
			Lines[Index].Widget->RemoveFromParent();
			Lines.RemoveAt(Index);
			continue;
		}
		const float FadeStart = LineLifetime - FadeTime;
		Lines[Index].Widget->SetRenderOpacity(Age > FadeStart ? float((LineLifetime - Age) / FMath::Max(FadeTime, 0.01f)) : 1.0f);
	}
	if (Lines.IsEmpty())
	{
		GetWorld()->GetTimerManager().ClearTimer(FadeTimer);
	}
}
