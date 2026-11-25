// See KochBallisticsSubsystem.h.

#include "Combat/KochBallisticsSubsystem.h"
#include "Combat/KochImpactEffects.h"
#include "Combat/KochPhysicalMaterial.h"
#include "Components/PrimitiveComponent.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"

bool UKochBallisticsSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId UKochBallisticsSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UKochBallisticsSubsystem, STATGROUP_Tickables);
}

void UKochBallisticsSubsystem::FireBullet(const FKochBulletSpec& Spec, const FVector& Start, const FVector& Direction, AActor* Shooter, FName NoiseTag)
{
	const UWorld* World = GetWorld();
	const FVector UnitDirection = Direction.GetSafeNormal();
	if (!World || UnitDirection.IsZero())
	{
		return;
	}

	FKochBullet Bullet;
	Bullet.Spec = Spec;
	Bullet.Shooter = Shooter;
	Bullet.Position = Start;
	Bullet.Velocity = UnitDirection * Spec.MuzzleSpeed;
	Bullet.RangeLeft = Spec.MaxRange;
	Bullet.NoiseTag = NoiseTag;

	// stepped as a local first: a damage callback may fire again and grow the arrays
	const float FirstStep = FMath::Clamp(World->GetDeltaSeconds(), 1.0f / 120.0f, 1.0f / 30.0f);
	if (!StepBullet(Bullet, FirstStep))
	{
		return;
	}

	if (bStepping)
	{
		PendingBullets.Add(MoveTemp(Bullet));
		return;
	}

	if (Bullets.Num() >= MaxBullets)
	{
		Bullets.RemoveAtSwap(0, EAllowShrinking::No);
	}
	Bullets.Add(MoveTemp(Bullet));
}

void UKochBallisticsSubsystem::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	bStepping = true;
	for (int32 Index = Bullets.Num() - 1; Index >= 0; --Index)
	{
		if (!StepBullet(Bullets[Index], DeltaTime))
		{
			Bullets.RemoveAtSwap(Index, EAllowShrinking::No);
		}
	}
	bStepping = false;

	if (PendingBullets.Num() > 0)
	{
		Bullets.Append(PendingBullets);
		PendingBullets.Reset();
	}
}

bool UKochBallisticsSubsystem::StepBullet(FKochBullet& Bullet, float DeltaTime)
{
	const UWorld* World = GetWorld();
	const FVector Gravity(0.0, 0.0, World->GetGravityZ() * Bullet.Spec.GravityScale);

	// complex trace: exact surface on static meshes (and their render-material physical material); skeletal meshes still answer with physics-asset bodies
	FCollisionQueryParams Params(SCENE_QUERY_STAT(KochBullet), true, Bullet.Shooter.Get());
	Params.bReturnPhysicalMaterial = true;

	float TimeLeft = DeltaTime;
	for (int32 HitCount = 0; HitCount < MaxHitsPerStep && TimeLeft > UE_KINDA_SMALL_NUMBER; ++HitCount)
	{
		// midpoint integration of the gravity arc over the rest of the step
		const FVector Start = Bullet.Position;
		const FVector EndVelocity = Bullet.Velocity + Gravity * TimeLeft;
		FVector Delta = (Bullet.Velocity + EndVelocity) * (0.5f * TimeLeft);
		double Length = Delta.Size();
		if (Length <= UE_KINDA_SMALL_NUMBER)
		{
			return false;
		}

		const bool bEndOfRange = Length >= Bullet.RangeLeft;
		if (bEndOfRange)
		{
			Delta *= Bullet.RangeLeft / Length;
			Length = Bullet.RangeLeft;
		}

		FHitResult Hit;
		if (!World->LineTraceSingleByChannel(Hit, Start, Start + Delta, Koch::BulletChannel, Params))
		{
			Bullet.Position = Start + Delta;
			Bullet.Velocity = EndVelocity;
			Bullet.RangeLeft -= Length;
			return !bEndOfRange;
		}

		Bullet.Velocity += Gravity * (TimeLeft * Hit.Time);
		Bullet.RangeLeft -= Hit.Distance;
		TimeLeft *= 1.0f - Hit.Time;

		// false: stopped. true: went through, Position is the exit point and the rest of the step continues from there
		if (!HandleImpact(Bullet, Hit, Delta / Length) || Bullet.RangeLeft <= 0.0f)
		{
			return false;
		}
	}

	// alive only if the step ran out of time, not out of hits
	return TimeLeft <= UE_KINDA_SMALL_NUMBER;
}

bool UKochBallisticsSubsystem::HandleImpact(FKochBullet& Bullet, const FHitResult& Hit, const FVector& Direction)
{
	const FKochBulletSpec& Spec = Bullet.Spec;
	AActor* Shooter = Bullet.Shooter.Get();
	APawn* ShooterPawn = Cast<APawn>(Shooter);
	AActor* HitActor = Hit.GetActor();
	UPrimitiveComponent* HitComponent = Hit.GetComponent();
	const UKochPhysicalMaterial* Material = Cast<UKochPhysicalMaterial>(Hit.PhysMaterial.Get());

	// pawns bleed whatever their physics asset says
	const bool bFlesh = Cast<APawn>(HitActor) != nullptr;
	const EKochSurface Surface = bFlesh ? EKochSurface::Flesh : (Material ? Material->Surface : EKochSurface::Default);
	UKochImpactSubsystem* Impacts = Spec.ImpactEffects ? GetWorld()->GetSubsystem<UKochImpactSubsystem>() : nullptr;

	// effects and the exit test run before damage: damage may ragdoll or destroy what was hit
	if (Impacts)
	{
		Impacts->PlayImpact(*Spec.ImpactEffects, Hit, Direction, Surface);
	}

	// > 0: the bullet goes through and keeps this share of its energy
	float EnergyKept = 0.0f;
	float Thickness = 0.0f;
	FVector ExitPoint = FVector::ZeroVector;

	const float MaxDepth = (!bFlesh && Material) ? Material->PenetrationDepth * Spec.PenetrationPower * Bullet.Energy : 0.0f;
	if (MaxDepth > 0.0f && HitComponent)
	{
		// trace back from beyond the far side; no hit, or a start inside the solid, means it is thicker than MaxDepth
		FHitResult Exit;
		const FCollisionQueryParams ExitParams(SCENE_QUERY_STAT(KochBulletExit), true);
		const FVector Beyond = Hit.ImpactPoint + Direction * (MaxDepth + 1.0f);
		if (HitComponent->LineTraceComponent(Exit, Beyond, Hit.ImpactPoint, ExitParams) && !Exit.bStartPenetrating)
		{
			Thickness = FVector::Dist(Hit.ImpactPoint, Exit.ImpactPoint);
			const float Kept = 1.0f - Thickness / MaxDepth;
			if (Kept > MinEnergyToExit)
			{
				EnergyKept = Kept;
				ExitPoint = Exit.ImpactPoint;
				if (Impacts)
				{
					Impacts->PlayImpact(*Spec.ImpactEffects, Exit, -Direction, Surface);
				}
			}
		}
	}

	const float HitEnergy = Bullet.Energy;

	if (HitComponent && HitComponent->IsSimulatingPhysics(Hit.BoneName))
	{
		HitComponent->AddImpulseAtLocation(Direction * (Spec.PhysicsImpulse * HitEnergy), Hit.ImpactPoint, Hit.BoneName);
	}

	if (ShooterPawn)
	{
		Shooter->MakeNoise(Spec.ImpactNoiseLoudness, ShooterPawn, Hit.ImpactPoint, Spec.ImpactNoiseRange, Bullet.NoiseTag);
	}

	// last use of HitActor and HitComponent: either may be gone after this
	if (HitActor && HitActor->CanBeDamaged())
	{
		UGameplayStatics::ApplyPointDamage(HitActor, Spec.Damage * HitEnergy, Direction, Hit, ShooterPawn ? ShooterPawn->GetController() : nullptr, Shooter, Spec.DamageType);
	}

	if (EnergyKept <= 0.0f)
	{
		return false;
	}

	// kinetic energy ~ v^2; restart 1 cm clear of the exit surface
	Bullet.Energy = HitEnergy * EnergyKept;
	Bullet.Velocity *= FMath::Sqrt(EnergyKept);
	Bullet.Position = ExitPoint + Direction;
	Bullet.RangeLeft -= Thickness;
	return true;
}
