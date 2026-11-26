// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "Logging/LogMacros.h"
#include "KochSimulatorCharacter.generated.h"

class UInputComponent;
class USkeletalMeshComponent;
class UCameraComponent;
class UInputAction;
class UInputMappingContext;
struct FInputActionValue;

DECLARE_LOG_CATEGORY_EXTERN(LogTemplateCharacter, Log, All);

/**
 *  A basic first person character
 */
UCLASS(abstract)
class AKochSimulatorCharacter : public ACharacter
{
	GENERATED_BODY()

	/** Pawn mesh: first person view (arms; seen only by self) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta = (AllowPrivateAccess = "true"))
	USkeletalMeshComponent* FirstPersonMesh;

	/** First person camera */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta = (AllowPrivateAccess = "true"))
	UCameraComponent* FirstPersonCameraComponent;

protected:

	/** Jump Input Action */
	UPROPERTY(EditAnywhere, Category ="Input")
	UInputAction* JumpAction;

	/** Move Input Action */
	UPROPERTY(EditAnywhere, Category ="Input")
	UInputAction* MoveAction;

	/** Look Input Action */
	UPROPERTY(EditAnywhere, Category ="Input")
	class UInputAction* LookAction;

	/** Mouse Look Input Action */
	UPROPERTY(EditAnywhere, Category ="Input")
	class UInputAction* MouseLookAction;

	/** Walk (hold): slower and silent to AI hearing, like CS Shift-walk */
	UPROPERTY(EditAnywhere, Category ="Input")
	UInputAction* WalkAction;

	/** Crouch (hold): slowest, silent, more accurate */
	UPROPERTY(EditAnywhere, Category ="Input")
	UInputAction* CrouchAction;

	/** Mapping context for walk/crouch, added when a local player possesses this pawn (template contexts stay untouched) */
	UPROPERTY(EditAnywhere, Category ="Input")
	UInputMappingContext* MovementMappingContext;

	/** Walk speed as a fraction of run speed (CS2 ~0.52) */
	UPROPERTY(EditAnywhere, Category ="Movement", meta = (ClampMin = 0.1, ClampMax = 1))
	float WalkSpeedScale = 0.52f;

	/** Crouch speed as a fraction of run speed (CS2 ~0.34) */
	UPROPERTY(EditAnywhere, Category ="Movement", meta = (ClampMin = 0.1, ClampMax = 1))
	float CrouchSpeedScale = 0.34f;
	
public:
	AKochSimulatorCharacter();

protected:

	/** Called from Input Actions for movement input */
	void MoveInput(const FInputActionValue& Value);

	/** Called from Input Actions for looking input */
	void LookInput(const FInputActionValue& Value);

	/** Handles aim inputs from either controls or UI interfaces */
	UFUNCTION(BlueprintCallable, Category="Input")
	virtual void DoAim(float Yaw, float Pitch);

	/** Handles move inputs from either controls or UI interfaces */
	UFUNCTION(BlueprintCallable, Category="Input")
	virtual void DoMove(float Right, float Forward);

	/** Handles jump start inputs from either controls or UI interfaces */
	UFUNCTION(BlueprintCallable, Category="Input")
	virtual void DoJumpStart();

	/** Handles jump end inputs from either controls or UI interfaces */
	UFUNCTION(BlueprintCallable, Category="Input")
	virtual void DoJumpEnd();

	UFUNCTION(BlueprintCallable, Category="Input")
	void DoWalkStart();

	UFUNCTION(BlueprintCallable, Category="Input")
	void DoWalkEnd();

	UFUNCTION(BlueprintCallable, Category="Input")
	void DoCrouchStart();

	UFUNCTION(BlueprintCallable, Category="Input")
	void DoCrouchEnd();

	/** Adds MovementMappingContext and sets walk/crouch speeds for local players */
	virtual void NotifyControllerChanged() override;

protected:

	/** Set up input action bindings */
	virtual void SetupPlayerInputComponent(UInputComponent* InputComponent) override;
	

public:

	/** Returns the first person mesh **/
	USkeletalMeshComponent* GetFirstPersonMesh() const { return FirstPersonMesh; }

	/** True while the walk key is held (AI treats walking as silent) */
	bool IsWalking() const { return bWalking; }

	/** Returns first person camera component **/
	UCameraComponent* GetFirstPersonCameraComponent() const { return FirstPersonCameraComponent; }


private:
	/** Run speed captured when a local player takes control (cm/s) */
	float RunSpeed = 0.0f;
	bool bWalking = false;
};
