#include "NightFallCharacter.h"

#include "Camera/CameraComponent.h"
#include "Components/InputComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "Net/UnrealNetwork.h"
#include "NightFall.h"

ANightFallCharacter::ANightFallCharacter()
{
	PrimaryActorTick.bCanEverTick = false;

	bUseControllerRotationYaw = false;
	GetCharacterMovement()->bOrientRotationToMovement = true;
	GetCharacterMovement()->RotationRate = FRotator(0.0f, 540.0f, 0.0f);
	GetCharacterMovement()->JumpZVelocity = 420.0f;
	GetCharacterMovement()->AirControl = 0.35f;
	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
	GetCharacterMovement()->MaxWalkSpeedCrouched = CrouchSpeed;
	GetCharacterMovement()->GetNavAgentPropertiesRef().bCanCrouch = true;

	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(GetRootComponent());
	CameraBoom->TargetArmLength = 320.0f;
	CameraBoom->SocketOffset = FVector(0.0f, 45.0f, 55.0f);
	CameraBoom->bUsePawnControlRotation = true;

	FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
	FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	FollowCamera->bUsePawnControlRotation = false;

	DefaultMappingContext = CreateDefaultSubobject<UInputMappingContext>(TEXT("DefaultMappingContext"));

	MoveForwardAction = CreateDefaultSubobject<UInputAction>(TEXT("MoveForwardAction"));
	MoveForwardAction->ValueType = EInputActionValueType::Axis1D;
	MoveRightAction = CreateDefaultSubobject<UInputAction>(TEXT("MoveRightAction"));
	MoveRightAction->ValueType = EInputActionValueType::Axis1D;
	LookAction = CreateDefaultSubobject<UInputAction>(TEXT("LookAction"));
	LookAction->ValueType = EInputActionValueType::Axis2D;
	JumpAction = CreateDefaultSubobject<UInputAction>(TEXT("JumpAction"));
	SprintAction = CreateDefaultSubobject<UInputAction>(TEXT("SprintAction"));
	CrouchAction = CreateDefaultSubobject<UInputAction>(TEXT("CrouchAction"));

	DefaultMappingContext->MapKey(MoveForwardAction, EKeys::W);
	FEnhancedActionKeyMapping& MoveBackwardMapping = DefaultMappingContext->MapKey(MoveForwardAction, EKeys::S);
	MoveBackwardMapping.Modifiers.Add(NewObject<UInputModifierNegate>(DefaultMappingContext));

	DefaultMappingContext->MapKey(MoveRightAction, EKeys::D);
	FEnhancedActionKeyMapping& MoveLeftMapping = DefaultMappingContext->MapKey(MoveRightAction, EKeys::A);
	MoveLeftMapping.Modifiers.Add(NewObject<UInputModifierNegate>(DefaultMappingContext));

	DefaultMappingContext->MapKey(LookAction, EKeys::Mouse2D);
	DefaultMappingContext->MapKey(JumpAction, EKeys::SpaceBar);
	DefaultMappingContext->MapKey(SprintAction, EKeys::LeftShift);
	DefaultMappingContext->MapKey(CrouchAction, EKeys::LeftControl);
}

void ANightFallCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	UEnhancedInputComponent* EnhancedInput = CastChecked<UEnhancedInputComponent>(PlayerInputComponent);

	EnhancedInput->BindAction(MoveForwardAction, ETriggerEvent::Triggered, this, &ANightFallCharacter::MoveForward);
	EnhancedInput->BindAction(MoveRightAction, ETriggerEvent::Triggered, this, &ANightFallCharacter::MoveRight);
	EnhancedInput->BindAction(LookAction, ETriggerEvent::Triggered, this, &ANightFallCharacter::Look);
	EnhancedInput->BindAction(JumpAction, ETriggerEvent::Started, this, &ANightFallCharacter::Jump);
	EnhancedInput->BindAction(JumpAction, ETriggerEvent::Completed, this, &ANightFallCharacter::StopJumping);
	EnhancedInput->BindAction(SprintAction, ETriggerEvent::Started, this, &ANightFallCharacter::StartSprint);
	EnhancedInput->BindAction(SprintAction, ETriggerEvent::Completed, this, &ANightFallCharacter::StopSprint);
	EnhancedInput->BindAction(CrouchAction, ETriggerEvent::Started, this, &ANightFallCharacter::ToggleCrouch);
}

void ANightFallCharacter::PossessedBy(AController* NewController)
{
	Super::PossessedBy(NewController);
	AddDefaultInputContext();

	if (HasAuthority())
	{
		UE_LOG(LogNightFall, Log, TEXT("NightFall: player pawn possessed by %s"), *GetNameSafe(NewController));
	}
}

void ANightFallCharacter::OnRep_PlayerState()
{
	Super::OnRep_PlayerState();
	AddDefaultInputContext();
}

void ANightFallCharacter::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(ANightFallCharacter, bIsSprinting);
}

void ANightFallCharacter::AddDefaultInputContext()
{
	const APlayerController* PlayerController = Cast<APlayerController>(GetController());
	if (!PlayerController)
	{
		return;
	}

	ULocalPlayer* LocalPlayer = PlayerController->GetLocalPlayer();
	if (!LocalPlayer)
	{
		return;
	}

	UEnhancedInputLocalPlayerSubsystem* Subsystem = LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>();
	if (Subsystem)
	{
		Subsystem->AddMappingContext(DefaultMappingContext, 0);
	}
}

float ANightFallCharacter::GetMaxWalkSpeedForState() const
{
	return bIsSprinting ? SprintSpeed : WalkSpeed;
}

void ANightFallCharacter::ApplyMovementSpeed()
{
	GetCharacterMovement()->MaxWalkSpeed = GetMaxWalkSpeedForState();
}

void ANightFallCharacter::SetSprinting(bool bNewSprinting)
{
	if (bIsSprinting == bNewSprinting)
	{
		return;
	}

	bIsSprinting = bNewSprinting;
	ApplyMovementSpeed();

	if (!HasAuthority())
	{
		ServerSetSprinting(bNewSprinting);
	}
}

void ANightFallCharacter::ServerSetSprinting_Implementation(bool bNewSprinting)
{
	bIsSprinting = bNewSprinting;
	ApplyMovementSpeed();
}

void ANightFallCharacter::OnRep_IsSprinting()
{
	ApplyMovementSpeed();
}

void ANightFallCharacter::SetCrouching(bool bNewCrouching)
{
	if (bNewCrouching)
	{
		Crouch();
	}
	else
	{
		UnCrouch();
	}

	if (!HasAuthority())
	{
		ServerSetCrouching(bNewCrouching);
	}
}

void ANightFallCharacter::ServerSetCrouching_Implementation(bool bNewCrouching)
{
	if (bNewCrouching)
	{
		Crouch();
	}
	else
	{
		UnCrouch();
	}
}

void ANightFallCharacter::MoveForward(const FInputActionValue& Value)
{
	const float AxisValue = Value.Get<float>();
	if (FMath::IsNearlyZero(AxisValue))
	{
		return;
	}

	const FRotationMatrix DirectionMatrix(FRotator(0.0f, GetControlRotation().Yaw, 0.0f));
	AddMovementInput(DirectionMatrix.GetUnitAxis(EAxis::X), AxisValue);
}

void ANightFallCharacter::MoveRight(const FInputActionValue& Value)
{
	const float AxisValue = Value.Get<float>();
	if (FMath::IsNearlyZero(AxisValue))
	{
		return;
	}

	const FRotationMatrix DirectionMatrix(FRotator(0.0f, GetControlRotation().Yaw, 0.0f));
	AddMovementInput(DirectionMatrix.GetUnitAxis(EAxis::Y), AxisValue);
}

void ANightFallCharacter::Look(const FInputActionValue& Value)
{
	const FVector2D AxisValue = Value.Get<FVector2D>();

	if (APlayerController* PlayerController = Cast<APlayerController>(GetController()))
	{
		PlayerController->AddYawInput(AxisValue.X);
		PlayerController->AddPitchInput(AxisValue.Y);
	}
}

void ANightFallCharacter::StartSprint()
{
	SetSprinting(true);
}

void ANightFallCharacter::StopSprint()
{
	SetSprinting(false);
}

void ANightFallCharacter::ToggleCrouch()
{
	SetCrouching(!bIsCrouched);
}
