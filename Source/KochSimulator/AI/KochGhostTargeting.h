// Pure Pac-Man ghost targeting + phase schedule math (no UObjects), unit-tested in KochGhostTargetingTests.cpp.
// Rules adapted from J. Pittman, "The Pac-Man Dossier": https://pacman.holenet.info/

#pragma once

#include "CoreMinimal.h"
#include "KochEnemyTypes.h"

namespace KochGhost
{
	/** Where an enemy with this role should move to now (not yet projected to the navmesh). */
	KOCHSIMULATOR_API FVector ComputeRoleTarget(EKochGhostRole Role, const FKochRoleTargetInput& In, const FKochRoleTargetParams& Params = FKochRoleTargetParams());

	/**
	 * Regroup/Chase durations in seconds, starting with Regroup and alternating.
	 * The last entry is negative = that phase lasts forever.
	 * Easy = Pac-Man level 1, Medium = levels 2-4, Hard = level 5+ (the 1033 s / 1 s steps collapse to "chase forever").
	 */
	KOCHSIMULATOR_API TConstArrayView<float> GetPhaseSchedule(EKochDifficulty Difficulty);

	/** Phase for step index Step of the schedule (even = Regroup, odd = Chase). */
	inline EKochSquadPhase PhaseForStep(int32 Step) { return (Step % 2 == 0) ? EKochSquadPhase::Regroup : EKochSquadPhase::Chase; }
}
