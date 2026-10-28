#include "Variant_Shooter/Companion/KochCompanion.h"
#include "AIController.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"

AKochCompanion::AKochCompanion()
{
	PrimaryActorTick.bCanEverTick = true;

	GetCapsuleComponent()->InitCapsuleSize(32.0f, 88.0f);

	BodyMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
	BodyMesh->SetupAttachment(GetCapsuleComponent());
	BodyMesh->SetRelativeLocation(FVector(0.0f, 0.0f, -88.0f));
	BodyMesh->SetCollisionProfileName(FName("NoCollision"));    // the capsule takes the hits

	// mannequin-rigged body: feet on the capsule bottom, facing +X like the template characters
	GetMesh()->SetRelativeLocationAndRotation(FVector(0.0f, 0.0f, -88.0f), FRotator(0.0f, -90.0f, 0.0f));
	GetMesh()->SetCollisionProfileName(FName("NoCollision"));

	GetCharacterMovement()->MaxWalkSpeed = 520.0f;
	GetCharacterMovement()->bOrientRotationToMovement = true;
	GetCharacterMovement()->RotationRate = FRotator(0.0f, 540.0f, 0.0f);
	bUseControllerRotationYaw = false;

	// possessed so the movement component consumes AddMovementInput
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;
	AIControllerClass = AAIController::StaticClass();
}

void AKochCompanion::BeginPlay()
{
	Super::BeginPlay();
	Target = UGameplayStatics::GetPlayerPawn(this, 0);
	BodyMesh->SetRelativeRotation(FRotator(0.0f, BodyYaw, 0.0f));
	bSkeletal = GetMesh()->GetSkeletalMeshAsset() != nullptr;
	BodyMesh->SetVisibility(!bSkeletal);
}

void AKochCompanion::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	APawn* Player = Target.Get();
	if (!Player)
	{
		Target = UGameplayStatics::GetPlayerPawn(this, 0);   // the player respawned
		return;
	}

	FVector ToPlayer = Player->GetActorLocation() - GetActorLocation();
	ToPlayer.Z = 0.0f;
	const float Dist = ToPlayer.Size();
	if (Dist > TeleportDistance)
	{
		const FVector Behind = Player->GetActorLocation() - Player->GetActorForwardVector() * FollowDistance;
		SetActorLocation(Behind, false, nullptr, ETeleportType::TeleportPhysics);
	}
	else if (Dist > FollowDistance + FollowSlack || (Dist > FollowDistance && GetVelocity().SizeSquared2D() > 100.0f))
	{
		AddMovementInput(ToPlayer / Dist, 1.0f);
	}
	else if (Dist > 1.0f)
	{
		// standing: turn to face the player
		const FRotator Want(0.0f, ToPlayer.Rotation().Yaw, 0.0f);
		SetActorRotation(FMath::RInterpTo(GetActorRotation(), Want, DeltaSeconds, 4.0f));
	}

	if (bSkeletal)
	{
		return;   // the anim BP walks it
	}

	// procedural walk: one bob per step, sway per stride, lean into the speed
	const float Speed = GetVelocity().Size2D();
	const float Alpha = FMath::Clamp(Speed / GetCharacterMovement()->MaxWalkSpeed, 0.0f, 1.0f);
	StepPhase = FMath::Fmod(StepPhase + DeltaSeconds * Speed / StrideLength * UE_PI, 2.0f * UE_PI);
	const float Bob = FMath::Abs(FMath::Sin(StepPhase)) * BobHeight * Alpha;
	const float Sway = FMath::Sin(StepPhase) * SwayAngle * Alpha;
	BodyMesh->SetRelativeLocationAndRotation(FVector(0.0f, 0.0f, -88.0f + Bob), FRotator(-LeanAngle * Alpha, BodyYaw, Sway));
}

float AKochCompanion::TakeDamage(float Damage, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
	if (!bDead && Damage > 0.0f)
	{
		bDead = true;
		Explode();
	}
	return Damage;
}

void AKochCompanion::Explode()
{
	UWorld* World = GetWorld();
	const FVector Centre = GetActorLocation();
	if (ExplosionClass)
	{
		World->SpawnActor<AActor>(ExplosionClass, FTransform(Centre));
	}
	if (DebrisMesh)
	{
		UMaterialInterface* Mat = bSkeletal ? GetMesh()->GetMaterial(0) : BodyMesh->GetMaterial(0);
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		for (int32 i = 0; i < DebrisCount; ++i)
		{
			const FVector Loc = Centre + FVector(FMath::FRandRange(-20.0f, 20.0f), FMath::FRandRange(-20.0f, 20.0f), FMath::FRandRange(-80.0f, 80.0f));
			AStaticMeshActor* Chunk = World->SpawnActor<AStaticMeshActor>(Loc, FRotator(FMath::FRandRange(0.0f, 360.0f), FMath::FRandRange(0.0f, 360.0f), 0.0f), Params);
			if (!Chunk)
			{
				continue;
			}
			Chunk->SetLifeSpan(DebrisLifeSpan * FMath::FRandRange(0.8f, 1.2f));
			UStaticMeshComponent* M = Chunk->GetStaticMeshComponent();
			M->SetMobility(EComponentMobility::Movable);
			M->SetStaticMesh(DebrisMesh);
			M->SetMaterial(0, Mat);
			M->SetWorldScale3D(FVector(FMath::FRandRange(0.06f, 0.16f)));   // 6..16 cm chunks of the 100 cm cube
			M->SetCollisionProfileName(FName("PhysicsActor"));
			M->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
			M->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
			M->SetSimulatePhysics(true);
			const FVector Out = (Loc - Centre).GetSafeNormal() + FVector(0.0f, 0.0f, 0.6f);
			M->SetPhysicsLinearVelocity(Out.GetSafeNormal() * DebrisSpeed * FMath::FRandRange(0.6f, 1.2f));
			M->SetPhysicsAngularVelocityInDegrees(FMath::VRand() * 720.0f);
		}
	}
	Destroy();
}
