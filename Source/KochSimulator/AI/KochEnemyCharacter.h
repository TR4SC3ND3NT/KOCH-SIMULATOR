// Hostile NPC for the KOCH squad: Pac-Man role, per-difficulty tuning, CS-style "accurate only when nearly stopped" aim.
// Thin BP children (BP_Enemy_Guard/Interceptor/Flanker/Heavy/Donk) set mesh, weapon, GhostRole, Tuning and BodyScale.

#pragma once

#include "CoreMinimal.h"
#include "ShooterNPC.h"
#include "KochEnemyTypes.h"
#include "KochEnemyCharacter.generated.h"

class UKochAwarenessComponent;
class UAnimMontage;
class USoundBase;

UCLASS(abstract)
class KOCHSIMULATOR_API AKochEnemyCharacter : public AShooterNPC
{
	GENERATED_BODY()

public:
	AKochEnemyCharacter();

	EKochGhostRole GetRole() const { return GhostRole; }
	const FKochEnemyTuning& GetActiveTuning() const { return ActiveTuning; }
	FVector GetAnchorLocation() const { return AnchorLocation; }
	bool IsAlive() const { return !bIsDead; }
	bool IsElroy() const { return bElroy; }
	UKochAwarenessComponent* GetAwareness() const { return Awareness; }
	const FText& GetDisplayName() const { return DisplayName; }
	float GetBurstDuration() const { return BurstDuration; }

	/** Temporary speed multiplier (StateTree: walk while suspicious/searching = quiet). 1 = run. */
	void SetMoveSpeedScale(float Scale);

	/** Called by UKochSquadSubsystem when only a few enemies are left (Pac-Man "Cruise Elroy"). */
	void SetElroy(bool bNewElroy);

	/** Overrides the Regroup point (default: spawn location). */
	UFUNCTION(BlueprintCallable, Category = "Koch|Squad")
	void SetAnchorLocation(const FVector& NewAnchor) { AnchorLocation = NewAnchor; }

	//~Begin IShooterWeaponHolder
	/** Widens the aim cone with move speed above AccurateSpeedRatio, narrows it while crouched. */
	virtual FVector GetWeaponTargetLocation() override;

	/** Like the template, but falls back to WeaponFallbackBone when the body lacks the grip socket (MetaHuman bodies). */
	virtual void AttachWeaponMeshes(AShooterWeapon* WeaponToAttach) override;

	/** The weapon calls this per shot and at reload start; plays FireMontage or ReloadMontage on the body. */
	virtual void PlayFiringMontage(UAnimMontage* Montage) override;
	//~End IShooterWeaponHolder

	virtual float TakeDamage(float Damage, struct FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser) override;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void PossessedBy(AController* NewController) override;
	virtual void UnPossessed() override;

	/** Plays a footstep when the stride is covered; silent when walking or crouched (CS rule). Timer, not Tick. */
	void UpdateFootsteps();

	UFUNCTION()
	void HandleDifficultyChanged(EKochDifficulty NewDifficulty);

	void ApplyTuning(EKochDifficulty Difficulty);
	void ApplyMoveSpeed();

	/** Trigger time of one "Koch Shoot Burst" (s); weapon-specific (pistol taps, LMG long bursts). 0 = the task's value. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Koch|Combat", meta = (ClampMin = 0, Units = "s"))
	float BurstDuration = 0.0f;

	/** Name in the kill feed (e.g. "Donk"). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Koch|UI")
	FText DisplayName = NSLOCTEXT("KochEnemy", "DefaultName", "Enemy");

	/** Pac-Man role that decides where this enemy moves. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Koch|Squad")
	EKochGhostRole GhostRole = EKochGhostRole::Chaser;

	/** Tuning per difficulty; missing entries fall back to FKochEnemyTuning defaults. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Koch|Tuning")
	TMap<EKochDifficulty, FKochEnemyTuning> Tuning;

	/** Uniform actor scale (Donk: built at 160 cm, 0.75 -> 120 cm). Capsule scales with it. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Koch|Body", meta = (ClampMin = 0.5, ClampMax = 1.5))
	float BodyScale = 1.0f;

	/** Bone used when the body mesh has no ThirdPersonWeaponSocket (MetaHuman skeletons ship without HandGrip_R). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Koch|Body")
	FName WeaponFallbackBone = FName("hand_r");

	/** Grip offset relative to WeaponFallbackBone; default = UE5 Manny's HandGrip_R socket (cm, degrees). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Koch|Body")
	FTransform WeaponFallbackOffset = FTransform(FRotator(0.0, 90.0, 0.0), FVector(-7.01, 2.05, 0.0));

	/** Extra speed while Elroy is active (0.1 = +10 %). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Koch|Squad", meta = (ClampMin = 0, ClampMax = 1))
	float ElroySpeedBonus = 0.1f;

	/** MetaHuman face: follows the body (leader pose). Grooms (hair, brows) attach to it in the BP. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Koch|Body")
	TObjectPtr<USkeletalMeshComponent> FaceMesh;

	/** MetaHuman outfit: follows the body (leader pose). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Koch|Body")
	TObjectPtr<USkeletalMeshComponent> OutfitMesh;

	/** Third-person shot kick, additive (Lyra AM_MM_Rifle_Fire, slot FullBodyAdditivePreAim). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Koch|Animation")
	TObjectPtr<UAnimMontage> FireMontage;

	/** Third-person reload (Lyra AM_MM_Rifle_Reload, slot UpperBody; carries the mag sounds). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Koch|Animation")
	TObjectPtr<UAnimMontage> ReloadMontage;

	/** Additive flinches by hit side (slot AdditiveHitReact); an empty side plays nothing. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Koch|Animation")
	TObjectPtr<UAnimMontage> HitReactFront;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Koch|Animation")
	TObjectPtr<UAnimMontage> HitReactBack;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Koch|Animation")
	TObjectPtr<UAnimMontage> HitReactLeft;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Koch|Animation")
	TObjectPtr<UAnimMontage> HitReactRight;

	/** Footstep sounds, picked at random (attenuation comes from the sound asset). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Koch|Sound")
	TArray<TObjectPtr<USoundBase>> FootstepSounds;

	/** Distance per footstep at BodyScale 1 (a jog stride is ~1.5 m); scaled by BodyScale. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Koch|Sound", meta = (ClampMin = 20, Units = "cm"))
	float FootstepStride = 150.0f;

	/** Steps are audible only above this fraction of RunSpeed (CS: shift-walk is silent). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Koch|Sound", meta = (ClampMin = 0, ClampMax = 1))
	float FootstepSpeedRatio = 0.6f;

	/** Senses, memory and awareness state (Unaware/Suspicious/Hunt/Engage/Search). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Koch|Awareness")
	TObjectPtr<UKochAwarenessComponent> Awareness;

private:
	FKochEnemyTuning ActiveTuning;
	float MoveSpeedScale = 1.0f;
	FVector AnchorLocation = FVector::ZeroVector;
	bool bElroy = false;
	bool bTuningApplied = false;
	FTimerHandle FootstepTimer;
	float FootstepDistance = 0.0f;
};
