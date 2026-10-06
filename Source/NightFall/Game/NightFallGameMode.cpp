#include "NightFallGameMode.h"

#include "Characters/NightFallCharacter.h"
#include "Game/NightFallGameState.h"

ANightFallGameMode::ANightFallGameMode()
{
	DefaultPawnClass = ANightFallCharacter::StaticClass();
	GameStateClass = ANightFallGameState::StaticClass();
}
