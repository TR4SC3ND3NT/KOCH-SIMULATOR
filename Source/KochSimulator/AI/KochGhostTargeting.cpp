// Pac-Man ghost targeting for a 3D navmesh FPS. See KochGhostTargeting.h.

#include "KochGhostTargeting.h"

namespace KochGhost
{
	namespace
	{
		/** Facing on the ground plane; falls back to +X so a player looking straight up/down still has a direction. */
		FVector GroundForward(const FVector& Forward)
		{
			const FVector Flat(Forward.X, Forward.Y, 0.0);
			return Flat.IsNearlyZero() ? FVector::ForwardVector : Flat.GetSafeNormal();
		}
	}

	FVector ComputeRoleTarget(EKochGhostRole Role, const FKochRoleTargetInput& In, const FKochRoleTargetParams& Params)
	{
		if (In.Phase == EKochSquadPhase::Regroup)
		{
			return In.AnchorLocation;
		}

		switch (Role)
		{
		case EKochGhostRole::Ambusher:
		{
			// Pinky: aim ahead of the player. Moving -> use velocity; standing -> use facing.
			FVector Lead(In.PlayerVelocity.X, In.PlayerVelocity.Y, 0.0);
			Lead *= Params.AmbushLeadTime;
			if (Lead.SizeSquared() < FMath::Square(Params.AmbushMinLead))
			{
				Lead = GroundForward(In.PlayerForward) * Params.AmbushMinLead;
			}
			return In.PlayerLocation + Lead;
		}

		case EKochGhostRole::Flanker:
		{
			// Inky: P = point ahead of the player; target = P + (P - Chaser) -> opposite side from the Chaser.
			const FVector Ahead = In.PlayerLocation + GroundForward(In.PlayerForward) * Params.FlankAheadDistance;
			if (!In.bHasLeader)
			{
				return Ahead;
			}
			FVector Mirror = Ahead - In.LeaderLocation;
			Mirror.Z = 0.0;
			Mirror = Mirror.GetClampedToMaxSize(Params.FlankMaxOffset);
			return Ahead + Mirror;
		}

		case EKochGhostRole::Shy:
		{
			// Clyde: chase only while far away.
			const double Dist2D = FVector::Dist2D(In.SelfLocation, In.PlayerLocation);
			return (Dist2D >= Params.ShyRadius) ? In.PlayerLocation : In.AnchorLocation;
		}

		case EKochGhostRole::Chaser:
		case EKochGhostRole::Peeker:
		default:
			return In.PlayerLocation;
		}
	}

	TConstArrayView<float> GetPhaseSchedule(EKochDifficulty Difficulty)
	{
		// R, C, R, C, ... (s); negative = forever.
		static const float Easy[]   = { 7.f, 20.f, 7.f, 20.f, 5.f, 20.f, 5.f, -1.f };
		static const float Medium[] = { 7.f, 20.f, 7.f, 20.f, 5.f, -1.f };
		static const float Hard[]   = { 5.f, 20.f, 5.f, 20.f, 5.f, -1.f };

		switch (Difficulty)
		{
		case EKochDifficulty::Easy:   return MakeArrayView(Easy);
		case EKochDifficulty::Hard:   return MakeArrayView(Hard);
		case EKochDifficulty::Medium:
		default:                      return MakeArrayView(Medium);
		}
	}
}
