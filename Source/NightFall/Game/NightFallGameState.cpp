#include "NightFallGameState.h"

#include "Net/UnrealNetwork.h"

ANightFallGameState::ANightFallGameState()
{
	SetNetUpdateFrequency(10.0f);
}

void ANightFallGameState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(ANightFallGameState, DayLengthSeconds);
}

float ANightFallGameState::GetDayPhase() const
{
	if (DayLengthSeconds <= 0.0f)
	{
		return 0.0f;
	}

	const double Elapsed = FMath::Fmod(GetServerWorldTimeSeconds(), static_cast<double>(DayLengthSeconds));
	return static_cast<float>(Elapsed / static_cast<double>(DayLengthSeconds));
}

float ANightFallGameState::GetTimeOfDayHours() const
{
	return GetDayPhase() * 24.0f;
}
