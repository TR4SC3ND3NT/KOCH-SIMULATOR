// Physical material with bullet data. Assign PM_Koch* assets to render materials or physics-asset bodies; read by UKochBallisticsSubsystem.
// Same idea as Lyra's UPhysicalMaterialWithTags (Epic sample), without Gameplay Tags.

#pragma once

#include "CoreMinimal.h"
#include "PhysicalMaterials/PhysicalMaterial.h"
#include "Combat/KochCombatTypes.h"
#include "KochPhysicalMaterial.generated.h"

UCLASS()
class KOCHSIMULATOR_API UKochPhysicalMaterial : public UPhysicalMaterial
{
	GENERATED_BODY()

public:

	/** Picks the impact effect. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Koch")
	EKochSurface Surface = EKochSurface::Default;

	/** Thickness (cm) a full-power rifle bullet (PenetrationPower 1) still passes through. 0 stops every bullet. Plasterboard ~12, wood ~8, brick ~3, steel plate ~0.5. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Koch", meta=(ClampMin=0, Units="cm"))
	float PenetrationDepth = 0.0f;
};
