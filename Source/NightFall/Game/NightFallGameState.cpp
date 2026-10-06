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
	DOREPLIFETIME(ANightFallGameState, StartDayPhase);
}

float ANightFallGameState::GetDayPhase() const
{
	if (DayLengthSeconds <= 0.0f)
	{
		return 0.0f;
	}

	const double DayLength = static_cast<double>(DayLengthSeconds);
	const double Elapsed = FMath::Fmod(GetServerWorldTimeSeconds() + static_cast<double>(StartDayPhase) * DayLength, DayLength);
	return static_cast<float>(Elapsed / DayLength);
}

float ANightFallGameState::GetTimeOfDayHours() const
{
	return GetDayPhase() * 24.0f;
}
