// Shared enemy-squad types: difficulty, Pac-Man ghost roles, squad phase, per-difficulty tuning.
// Used by UKochSquadSubsystem, AKochEnemyCharacter and the Koch StateTree tasks. Spec: docs/design/enemies.md

#pragma once

#include "CoreMinimal.h"
#include "KochEnemyTypes.generated.h"

/** Game difficulty picked in the menu (UKochDifficultySubsystem). */
UENUM(BlueprintType)
enum class EKochDifficulty : uint8
{
	Easy,
	Medium,
	Hard
};

/** Pac-Man ghost role that decides where an enemy goes (see KochGhost::ComputeRoleTarget). */
UENUM(BlueprintType)
enum class EKochGhostRole : uint8
{
	Chaser,   // Blinky: the player's current position
	Ambusher, // Pinky: where the player will be (position + velocity * lead time)
	Flanker,  // Inky: mirror of the Chaser through a point ahead of the player (pincer)
	Shy,      // Clyde: rushes from far, falls back to its anchor when close
	Peeker    // Donk: chases like Blinky, fights with CS-style peeks
};

/** Squad-wide phase, Pac-Man scatter/chase. */
UENUM(BlueprintType)
enum class EKochSquadPhase : uint8
{
	Regroup, // scatter: everyone heads to its own anchor
	Chase
};

/** What an enemy knows about the player (UKochAwarenessComponent). */
UENUM(BlueprintType)
enum class EKochAwareness : uint8
{
	Unaware,    // no information: idle / patrol at the anchor
	Suspicious, // heard something: walk over and look
	Hunt,       // player known but not visible: go to the role target around the last known position
	Engage,     // player visible (or lost < LoseSightGrace): hold a fighting position and shoot
	Search      // lost him: check the last known position and nearby spots, then give up
};

/** Per-difficulty tuning for one enemy type. Units: cm, cm/s, cm/s^2, s, degrees. */
USTRUCT(BlueprintType)
struct FKochEnemyTuning
{
	GENERATED_BODY()

	/** Delay between first seeing the target and the first shot (s). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = 0, Units = "s"))
	float ReactionTime = 0.35f;

	/** Aim cone half-angle when standing still / below the accurate-speed ratio. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = 0, ClampMax = 45, Units = "Degrees"))
	float AimConeStill = 3.5f;

	/** Aim cone half-angle at full run speed (CS: running shots are inaccurate). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = 0, ClampMax = 45, Units = "Degrees"))
	float AimConeRunning = 12.0f;

	/** Speed / MaxWalkSpeed below which shots use AimConeStill (CS2: 0.34). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = 0, ClampMax = 1))
	float AccurateSpeedRatio = 0.34f;

	/** Cone multiplier while crouched (CS2: about -25 % inaccuracy). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = 0, ClampMax = 1))
	float CrouchConeScale = 0.75f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = 0, Units = "cm/s"))
	float RunSpeed = 400.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = 0, Units = "cm/s"))
	float CrouchSpeed = 140.0f;

	/** Higher = sharper starts and counter-strafes (3400 gives a ~80 ms stop-to-accurate). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = 0))
	float MaxAcceleration = 2048.0f;

	/** Deceleration with no input (1350 gives ~200 ms from 410 to 140 cm/s). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = 0))
	float BrakingDeceleration = 2048.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = 1))
	float MaxHealth = 100.0f;

	/** Multiplies this enemy's hit damage on the player (balance knob per difficulty). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = 0))
	float DamageScale = 1.0f;

	/** False = this enemy does not spawn on this difficulty (spawners check it). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	bool bEnabled = true;

	// --- Awareness ---

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Awareness", meta = (ClampMin = 0, Units = "cm"))
	float SightRange = 3500.0f;

	/** Half-angle of the vision cone. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Awareness", meta = (ClampMin = 5, ClampMax = 180, Units = "Degrees"))
	float SightHalfAngle = 70.0f;

	/** Continuous visibility needed to notice the player while unaware (scaled down when close / already alert). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Awareness", meta = (ClampMin = 0, Units = "s"))
	float NoticeTime = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Awareness", meta = (ClampMin = 0, Units = "cm"))
	float HearingRange = 3000.0f;

	/** How long the last known position stays useful before switching to Search. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Awareness", meta = (ClampMin = 0, Units = "s"))
	float MemoryTime = 8.0f;

	/** How long to search before giving up. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Awareness", meta = (ClampMin = 0, Units = "s"))
	float SearchTime = 12.0f;

	/** Keeps engaging this long after losing sight before hunting (covers brief occlusion). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Awareness", meta = (ClampMin = 0, Units = "s"))
	float LoseSightGrace = 1.0f;

	/** Preferred fighting distance band. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Awareness", meta = (ClampMin = 0, Units = "cm"))
	float EngageRangeMin = 600.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Awareness", meta = (ClampMin = 0, Units = "cm"))
	float EngageRangeMax = 2000.0f;
};

/** What the squad believes about the player; drives role targets (never the true position unless seen). */
struct FKochTargetBelief
{
	FVector Location = FVector::ZeroVector;
	FVector Velocity = FVector::ZeroVector;
	FVector Forward = FVector::ForwardVector;
};

/** Inputs for KochGhost::ComputeRoleTarget. All positions in world space (cm). */
struct FKochRoleTargetInput
{
	FVector PlayerLocation = FVector::ZeroVector;
	FVector PlayerVelocity = FVector::ZeroVector;
	FVector PlayerForward = FVector::ForwardVector;
	FVector SelfLocation = FVector::ZeroVector;
	/** Squad Chaser used by the Flanker; ignored when bHasLeader is false. */
	FVector LeaderLocation = FVector::ZeroVector;
	bool bHasLeader = false;
	/** Regroup point for this enemy (its Pac-Man "corner"). */
	FVector AnchorLocation = FVector::ZeroVector;
	EKochSquadPhase Phase = EKochSquadPhase::Chase;
};

/** Role targeting constants (cm, s). Defaults map Pac-Man tile distances to ~1 m tiles. */
struct FKochRoleTargetParams
{
	/** Ambusher lead time (s); Pinky looks 4 tiles ahead. */
	float AmbushLeadTime = 1.75f;
	/** Minimum ambush lead along the player's facing when he stands still. */
	float AmbushMinLead = 400.0f;
	/** Flanker reference point ahead of the player (Inky: 2 tiles). */
	float FlankAheadDistance = 400.0f;
	/** Caps the Flanker's mirrored target so it does not run off across the map. */
	float FlankMaxOffset = 1500.0f;
	/** Shy enemies retreat inside this 2D distance (Clyde: 8 tiles). */
	float ShyRadius = 1200.0f;
};
