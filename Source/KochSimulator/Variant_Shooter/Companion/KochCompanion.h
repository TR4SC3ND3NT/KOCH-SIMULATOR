// Playtest companion (R4; owner request 2026-10-28), spawned by AShooterCharacter on T: walks after the player and
// blows apart when it takes any damage (a shot). With a skeletal mesh on the character Mesh (rigged to the mannequin
// skeleton, Scripts/Blender/rig_to_mannequin.py) the mannequin anim BP animates it; with only BodyMesh (unrigged
// static mesh) the walk is procedural: a step bob, a side sway and a forward lean scaled by speed. AI-possessed so the
// movement component runs; steering is direct (no navmesh in the greybox level), with a teleport catch-up when left
// far behind.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "KochCompanion.generated.h"

class UStaticMeshComponent;
class UStaticMesh;

UCLASS(abstract)
class KOCHSIMULATOR_API AKochCompanion : public ACharacter
{
	GENERATED_BODY()

	/** Visible body (static mesh, pivot at the feet), animated procedurally in Tick */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta = (AllowPrivateAccess = "true"))
	UStaticMeshComponent* BodyMesh;

public:

	AKochCompanion();

protected:

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual float TakeDamage(float Damage, struct FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser) override;

	/** Keeps this far from the player (cm); walks when farther than FollowDistance + FollowSlack */
	UPROPERTY(EditAnywhere, Category="Follow", meta = (ClampMin = 50, Units = "cm"))
	float FollowDistance = 220.0f;

	UPROPERTY(EditAnywhere, Category="Follow", meta = (ClampMin = 0, Units = "cm"))
	float FollowSlack = 80.0f;

	/** Farther than this the companion reappears behind the player */
	UPROPERTY(EditAnywhere, Category="Follow", meta = (ClampMin = 500, Units = "cm"))
	float TeleportDistance = 3000.0f;

	/** Yaw of the body mesh relative to the actor so its face looks along +X (depends on the source export) */
	UPROPERTY(EditAnywhere, Category="Body", meta = (Units = "Degrees"))
	float BodyYaw = -90.0f;

	/** Stride length used to time the step bob (cm per step) */
	UPROPERTY(EditAnywhere, Category="Body", meta = (ClampMin = 10, Units = "cm"))
	float StrideLength = 70.0f;

	UPROPERTY(EditAnywhere, Category="Body", meta = (ClampMin = 0, Units = "cm"))
	float BobHeight = 3.5f;

	UPROPERTY(EditAnywhere, Category="Body", meta = (ClampMin = 0, Units = "Degrees"))
	float SwayAngle = 4.0f;

	UPROPERTY(EditAnywhere, Category="Body", meta = (ClampMin = 0, Units = "Degrees"))
	float LeanAngle = 5.0f;

	/** Spawned at the body centre on death (e.g. the template grenade explosion) */
	UPROPERTY(EditAnywhere, Category="Death")
	TSubclassOf<AActor> ExplosionClass;

	/** Chunks flung out on death, in the body material */
	UPROPERTY(EditAnywhere, Category="Death")
	UStaticMesh* DebrisMesh;

	UPROPERTY(EditAnywhere, Category="Death", meta = (ClampMin = 0, ClampMax = 40))
	int32 DebrisCount = 16;

	UPROPERTY(EditAnywhere, Category="Death", meta = (ClampMin = 0, Units = "cm/s"))
	float DebrisSpeed = 900.0f;

	UPROPERTY(EditAnywhere, Category="Death", meta = (ClampMin = 0.5, ClampMax = 30, Units = "s"))
	float DebrisLifeSpan = 4.0f;

private:

	TWeakObjectPtr<APawn> Target;
	bool bSkeletal = false;
	float StepPhase = 0.0f;
	bool bDead = false;

	void Explode();
};
