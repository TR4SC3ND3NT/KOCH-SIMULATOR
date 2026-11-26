// Automation tests for the pure Pac-Man targeting + phase schedule (KochGhostTargeting.h).
// Run: UnrealEditor-Cmd KochSimulator.uproject -ExecCmds="Automation RunTests KochSimulator.AI;Quit" -unattended -nullrhi

#include "Misc/AutomationTest.h"
#include "KochGhostTargeting.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	FKochRoleTargetInput MakeInput()
	{
		FKochRoleTargetInput In;
		In.PlayerLocation = FVector(1000.0, 0.0, 100.0);
		In.PlayerForward = FVector(1.0, 0.0, 0.0);
		In.SelfLocation = FVector(0.0, 0.0, 100.0);
		In.AnchorLocation = FVector(-500.0, -500.0, 100.0);
		In.Phase = EKochSquadPhase::Chase;
		return In;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKochGhostTargetingTest, "KochSimulator.AI.GhostTargeting",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FKochGhostTargetingTest::RunTest(const FString& Parameters)
{
	const FKochRoleTargetParams Params;

	// Chaser and Peeker go straight for the player.
	{
		const FKochRoleTargetInput In = MakeInput();
		TestEqual(TEXT("Chaser -> player"), KochGhost::ComputeRoleTarget(EKochGhostRole::Chaser, In, Params), In.PlayerLocation);
		TestEqual(TEXT("Peeker -> player"), KochGhost::ComputeRoleTarget(EKochGhostRole::Peeker, In, Params), In.PlayerLocation);
	}

	// Regroup sends every role to its anchor.
	{
		FKochRoleTargetInput In = MakeInput();
		In.Phase = EKochSquadPhase::Regroup;
		TestEqual(TEXT("Regroup -> anchor"), KochGhost::ComputeRoleTarget(EKochGhostRole::Ambusher, In, Params), In.AnchorLocation);
	}

	// Ambusher: standing player -> AmbushMinLead along facing; moving player -> velocity * lead time.
	{
		FKochRoleTargetInput In = MakeInput();
		TestEqual(TEXT("Ambusher, standing"), KochGhost::ComputeRoleTarget(EKochGhostRole::Ambusher, In, Params),
			In.PlayerLocation + FVector(Params.AmbushMinLead, 0.0, 0.0));
		In.PlayerVelocity = FVector(0.0, 400.0, 0.0);
		TestEqual(TEXT("Ambusher, moving"), KochGhost::ComputeRoleTarget(EKochGhostRole::Ambusher, In, Params),
			In.PlayerLocation + FVector(0.0, 400.0 * Params.AmbushLeadTime, 0.0));
	}

	// Flanker: mirror of the leader through the point ahead of the player -> opposite side.
	{
		FKochRoleTargetInput In = MakeInput();
		In.bHasLeader = true;
		In.LeaderLocation = FVector(1400.0, -600.0, 100.0); // leader on the -Y side of the ahead point (1400, 0)
		const FVector Target = KochGhost::ComputeRoleTarget(EKochGhostRole::Flanker, In, Params);
		TestTrue(TEXT("Flanker on the opposite (+Y) side"), Target.Y > 0.0);
		TestEqual(TEXT("Flanker mirror"), Target, FVector(1400.0, 600.0, 100.0));

		In.LeaderLocation = FVector(1400.0, -10000.0, 100.0);
		const FVector Clamped = KochGhost::ComputeRoleTarget(EKochGhostRole::Flanker, In, Params);
		TestTrue(TEXT("Flanker offset clamped"), FVector::Dist2D(Clamped, FVector(1400.0, 0.0, 100.0)) <= Params.FlankMaxOffset + 0.01);
	}

	// Shy: chases from far, retreats to the anchor when close.
	{
		FKochRoleTargetInput In = MakeInput();
		In.SelfLocation = In.PlayerLocation + FVector(Params.ShyRadius + 100.0, 0.0, 0.0);
		TestEqual(TEXT("Shy far -> player"), KochGhost::ComputeRoleTarget(EKochGhostRole::Shy, In, Params), In.PlayerLocation);
		In.SelfLocation = In.PlayerLocation + FVector(200.0, 0.0, 0.0);
		TestEqual(TEXT("Shy close -> anchor"), KochGhost::ComputeRoleTarget(EKochGhostRole::Shy, In, Params), In.AnchorLocation);
	}

	// Schedules start with Regroup, alternate, and end in "chase forever".
	for (const EKochDifficulty Difficulty : { EKochDifficulty::Easy, EKochDifficulty::Medium, EKochDifficulty::Hard })
	{
		const TConstArrayView<float> Schedule = KochGhost::GetPhaseSchedule(Difficulty);
		TestTrue(TEXT("Schedule not empty"), Schedule.Num() > 1);
		TestTrue(TEXT("Last step is forever"), Schedule.Last() < 0.0f);
		TestEqual(TEXT("Last step is Chase"), KochGhost::PhaseForStep(Schedule.Num() - 1), EKochSquadPhase::Chase);
		TestEqual(TEXT("First step is Regroup"), KochGhost::PhaseForStep(0), EKochSquadPhase::Regroup);
	}
	TestEqual(TEXT("Hard opens with a 5 s regroup"), KochGhost::GetPhaseSchedule(EKochDifficulty::Hard)[0], 5.0f);

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
