#include "NightFallSunActor.h"

#include "NightFall.h"
#include "Components/DirectionalLightComponent.h"
#include "Game/NightFallGameState.h"

ANightFallSunActor::ANightFallSunActor()
{
	PrimaryActorTick.bCanEverTick = true;
	SetActorTickEnabled(true);

	SunLight = CreateDefaultSubobject<UDirectionalLightComponent>(TEXT("SunLight"));
	RootComponent = SunLight;
}

FRotator ANightFallSunActor::GetSunRotationForPhase(float Phase) const
{
	const float Elevation = FMath::Sin(2.0f * UE_PI * (Phase - 0.25f));
	return FRotator(90.0f * Elevation, SunYaw, 0.0f);
}

float ANightFallSunActor::GetSunIntensityForPhase(float Phase) const
{
	const float Elevation = FMath::Sin(2.0f * UE_PI * (Phase - 0.25f));
	return NoonIntensity * FMath::Clamp(Elevation, 0.0f, 1.0f);
}

void ANightFallSunActor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	const UWorld* World = GetWorld();
	const ANightFallGameState* GameState = World ? World->GetGameState<ANightFallGameState>() : nullptr;

	if (!World || !GameState)
	{
		return;
	}

	const float Phase = GameState->GetDayPhase();
	SetActorRotation(GetSunRotationForPhase(Phase));
	SunLight->SetIntensity(GetSunIntensityForPhase(Phase));
}
