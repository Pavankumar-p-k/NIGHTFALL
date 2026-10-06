#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameStateBase.h"
#include "NightFallGameState.generated.h"

UCLASS(config = Game)
class NIGHTFALL_API ANightFallGameState : public AGameStateBase
{
	GENERATED_BODY()

public:
	ANightFallGameState();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category = "Time", meta = (ClampMin = "60", ClampMax = "86400"))
	float DayLengthSeconds = 900.0f;

	UFUNCTION(BlueprintPure, Category = "Time")
	float GetDayPhase() const;

	UFUNCTION(BlueprintPure, Category = "Time")
	float GetTimeOfDayHours() const;
};
