#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "NightFall.h"
#include "AIController.h"
#include "Characters/NightFallCharacter.h"
#include "Components/BoxComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "CoreGlobals.h"
#include "Engine/Engine.h"
#include "Engine/EngineBaseTypes.h"
#include "Engine/World.h"
#include "Game/NightFallGameMode.h"
#include "Game/NightFallGameState.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/WorldSettings.h"
#include "Time/NightFallSunActor.h"
#include "UObject/UObjectGlobals.h"

namespace NightFallTests
{
	constexpr float FrameDeltaSeconds = 1.0f / 60.0f;
	uint64 CachedFrameCounter = 0;

	UWorld* CreateGameWorld()
	{
		FWorldContext& WorldContext = GEngine->CreateNewWorldContext(EWorldType::Game);
		const FName WorldName = MakeUniqueObjectName(nullptr, UWorld::StaticClass(), NAME_None, EUniqueObjectNameOptions::GloballyUnique);
		UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, WorldName, GetTransientPackage());
		if (!World)
		{
			return nullptr;
		}

		World->AddToRoot();
		WorldContext.SetCurrentWorld(World);
		CachedFrameCounter = GFrameCounter;

		World->InitializeActorsForPlay(FURL());
		World->BeginPlay();
		World->GetWorldSettings()->NotifyBeginPlay();
		return World;
	}

	void DestroyGameWorld(UWorld* World)
	{
		if (!World)
		{
			return;
		}

		World->EndPlay(EEndPlayReason::LevelTransition);
		GEngine->ShutdownWorldNetDriver(World);
		World->DestroyWorld(true);
		World->SetPhysicsScene(nullptr);
		GEngine->DestroyWorldContext(World);
		World->RemoveFromRoot();
		GFrameCounter = CachedFrameCounter;
	}

	void AddFloor(UWorld* World)
	{
		AActor* Floor = World->SpawnActor<AActor>(FVector::ZeroVector, FRotator::ZeroRotator);
		if (!Floor)
		{
			return;
		}

		UBoxComponent* FloorBox = NewObject<UBoxComponent>(Floor, TEXT("FloorCollision"));
		Floor->SetRootComponent(FloorBox);
		FloorBox->SetBoxExtent(FVector(4000.0f, 4000.0f, 50.0f));
		FloorBox->SetCollisionProfileName(TEXT("BlockAll"));
		FloorBox->RegisterComponentWithWorld(World);
		Floor->SetActorLocation(FVector(0.0f, 0.0f, -50.0f));
	}

	void TickWorld(UWorld* World, int32 NumFrames)
	{
		for (int32 Frame = 0; Frame < NumFrames; ++Frame)
		{
			World->Tick(LEVELTICK_All, FrameDeltaSeconds);
			GFrameCounter++;
		}
	}

	bool PossessCharacter(UWorld* World, APawn* Pawn)
	{
		if (!World || !Pawn)
		{
			return false;
		}

		AAIController* Controller = World->SpawnActor<AAIController>(FVector::ZeroVector, FRotator::ZeroRotator);
		if (!Controller)
		{
			return false;
		}

		Controller->Possess(Pawn);
		return Pawn->GetController() == Controller;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNightFallGameModeDefaultsTest, "NightFall.GameMode.DefaultClasses",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)

bool FNightFallGameModeDefaultsTest::RunTest(const FString& Parameters)
{
	const ANightFallGameMode* GameMode = GetDefault<ANightFallGameMode>();
	if (!GameMode)
	{
		AddError(TEXT("ANightFallGameMode CDO not found"));
		return false;
	}

	TestTrue(TEXT("Default pawn is ANightFallCharacter"), GameMode->DefaultPawnClass == ANightFallCharacter::StaticClass());
	TestTrue(TEXT("Game state is ANightFallGameState"), GameMode->GameStateClass == ANightFallGameState::StaticClass());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNightFallSprintSpeedTest, "NightFall.Character.SprintChangesWalkSpeed",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)

bool FNightFallSprintSpeedTest::RunTest(const FString& Parameters)
{
	UWorld* World = NightFallTests::CreateGameWorld();
	if (!World)
	{
		AddError(TEXT("Failed to create test world"));
		return false;
	}

	ANightFallCharacter* Character = World->SpawnActor<ANightFallCharacter>(FVector(0.0f, 0.0f, 200.0f), FRotator::ZeroRotator);
	if (!Character)
	{
		AddError(TEXT("Failed to spawn character"));
		NightFallTests::DestroyGameWorld(World);
		return false;
	}

	if (!NightFallTests::PossessCharacter(World, Character))
	{
		AddError(TEXT("Failed to possess character"));
		NightFallTests::DestroyGameWorld(World);
		return false;
	}

	TestTrue(TEXT("Spawned character has authority"), Character->HasAuthority());

	const float WalkingSpeed = Character->GetMaxWalkSpeedForState();
	TestTrue(TEXT("Walking speed matches configured WalkSpeed"), FMath::IsNearlyEqual(WalkingSpeed, Character->WalkSpeed));
	TestTrue(TEXT("Movement component is at walking speed"),
		FMath::IsNearlyEqual(Character->GetCharacterMovement()->MaxWalkSpeed, WalkingSpeed));

	Character->SetSprinting(true);
	TestTrue(TEXT("Sprint flag is set"), Character->bIsSprinting);
	TestTrue(TEXT("Sprinting speed matches configured SprintSpeed"),
		FMath::IsNearlyEqual(Character->GetMaxWalkSpeedForState(), Character->SprintSpeed));
	TestTrue(TEXT("Movement component is at sprint speed"),
		FMath::IsNearlyEqual(Character->GetCharacterMovement()->MaxWalkSpeed, Character->SprintSpeed));
	TestTrue(TEXT("Sprint is faster than walk"), Character->SprintSpeed > Character->WalkSpeed);

	Character->SetSprinting(false);
	TestFalse(TEXT("Sprint flag cleared"), Character->bIsSprinting);
	TestTrue(TEXT("Movement component returned to walk speed"),
		FMath::IsNearlyEqual(Character->GetCharacterMovement()->MaxWalkSpeed, WalkingSpeed));

	NightFallTests::DestroyGameWorld(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNightFallMovementInputTest, "NightFall.Character.ForwardInputMovesCharacter",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)

bool FNightFallMovementInputTest::RunTest(const FString& Parameters)
{
	UWorld* World = NightFallTests::CreateGameWorld();
	if (!World)
	{
		AddError(TEXT("Failed to create test world"));
		return false;
	}

	NightFallTests::AddFloor(World);

	ANightFallCharacter* Character = World->SpawnActor<ANightFallCharacter>(FVector(0.0f, 0.0f, 200.0f), FRotator::ZeroRotator);
	if (!Character)
	{
		AddError(TEXT("Failed to spawn character"));
		NightFallTests::DestroyGameWorld(World);
		return false;
	}

	if (!NightFallTests::PossessCharacter(World, Character))
	{
		AddError(TEXT("Failed to possess character"));
		NightFallTests::DestroyGameWorld(World);
		return false;
	}

	NightFallTests::TickWorld(World, 60);
	const FVector StartLocation = Character->GetActorLocation();
	TestTrue(TEXT("Character settled on the floor"), StartLocation.Z < 150.0f);

	for (int32 Frame = 0; Frame < 90; ++Frame)
	{
		Character->AddMovementInput(FVector(1.0f, 0.0f, 0.0f), 1.0f);
		NightFallTests::TickWorld(World, 1);
	}

	const FVector EndLocation = Character->GetActorLocation();
	TestTrue(TEXT("Character travelled forward"), EndLocation.X - StartLocation.X > 100.0f);
	TestTrue(TEXT("Character produced forward velocity"), Character->GetVelocity().X > 0.0f);

	NightFallTests::DestroyGameWorld(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNightFallCrouchTest, "NightFall.Character.CrouchAppliesOnAuthority",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)

bool FNightFallCrouchTest::RunTest(const FString& Parameters)
{
	UWorld* World = NightFallTests::CreateGameWorld();
	if (!World)
	{
		AddError(TEXT("Failed to create test world"));
		return false;
	}

	NightFallTests::AddFloor(World);

	ANightFallCharacter* Character = World->SpawnActor<ANightFallCharacter>(FVector(0.0f, 0.0f, 200.0f), FRotator::ZeroRotator);
	if (!Character)
	{
		AddError(TEXT("Failed to spawn character"));
		NightFallTests::DestroyGameWorld(World);
		return false;
	}

	if (!NightFallTests::PossessCharacter(World, Character))
	{
		AddError(TEXT("Failed to possess character"));
		NightFallTests::DestroyGameWorld(World);
		return false;
	}

	NightFallTests::TickWorld(World, 60);
	TestFalse(TEXT("Character starts standing"), Character->IsCrouched());

	Character->SetCrouching(true);
	NightFallTests::TickWorld(World, 30);
	TestTrue(TEXT("Character is crouched after input"), Character->IsCrouched());
	TestTrue(TEXT("Crouch speed is below walk speed"),
		Character->GetCharacterMovement()->MaxWalkSpeedCrouched < Character->WalkSpeed);

	Character->SetCrouching(false);
	NightFallTests::TickWorld(World, 30);
	TestFalse(TEXT("Character stands up after input"), Character->IsCrouched());

	NightFallTests::DestroyGameWorld(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNightFallDayNightTest, "NightFall.Time.DayPhaseDrivesSun",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)

bool FNightFallDayNightTest::RunTest(const FString& Parameters)
{
	UWorld* World = NightFallTests::CreateGameWorld();
	if (!World)
	{
		AddError(TEXT("Failed to create test world"));
		return false;
	}

	ANightFallGameState* GameState = World->SpawnActor<ANightFallGameState>(FVector::ZeroVector, FRotator::ZeroRotator);
	ANightFallSunActor* Sun = World->SpawnActor<ANightFallSunActor>(FVector(0.0f, 0.0f, 1000.0f), FRotator::ZeroRotator);
	if (!GameState || !Sun)
	{
		AddError(TEXT("Failed to spawn game state or sun actor"));
		NightFallTests::DestroyGameWorld(World);
		return false;
	}

	TestTrue(TEXT("Game state resolved by world"), World->GetGameState<ANightFallGameState>() == GameState);

	GameState->DayLengthSeconds = 4.0f;
	const FRotator InitialRotation = Sun->GetActorRotation();

	NightFallTests::TickWorld(World, 120);

	const float Phase = GameState->GetDayPhase();
	TestTrue(TEXT("Day phase advanced with world time"), Phase > 0.3f && Phase < 0.7f);
	TestTrue(TEXT("Time of day hours follow phase"), FMath::IsNearlyEqual(GameState->GetTimeOfDayHours(), Phase * 24.0f, 0.01f));

	const FRotator CurrentRotation = Sun->GetActorRotation();
	TestFalse(TEXT("Sun rotated with day phase"), CurrentRotation.Equals(InitialRotation, 1.0f));
	TestTrue(TEXT("Sun points near zenith at midday"), CurrentRotation.Pitch > 60.0f);
	TestTrue(TEXT("Sun light is lit at midday"), Sun->SunLight->Intensity > 0.0f);
	TestTrue(TEXT("Sun intensity equals noon intensity at midday"),
		FMath::IsNearlyEqual(Sun->SunLight->Intensity, Sun->NoonIntensity, 0.1f));

	TestEqual(TEXT("Sun intensity is zero at midnight"), Sun->GetSunIntensityForPhase(0.0f), 0.0f);
	TestEqual(TEXT("Sun intensity is zero at dawn"), Sun->GetSunIntensityForPhase(0.25f), 0.0f);
	TestTrue(TEXT("Sun intensity is full at midday"), FMath::IsNearlyEqual(Sun->GetSunIntensityForPhase(0.5f), Sun->NoonIntensity));
	TestTrue(TEXT("Sun is below horizon at midnight"), Sun->GetSunRotationForPhase(0.0f).Pitch < 0.0f);

	NightFallTests::DestroyGameWorld(World);
	return true;
}

#endif
