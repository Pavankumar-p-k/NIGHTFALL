#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NightFallSunActor.generated.h"

class UDirectionalLightComponent;

UCLASS()
class NIGHTFALL_API ANightFallSunActor : public AActor
{
	GENERATED_BODY()

public:
	ANightFallSunActor();

	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Sun")
	TObjectPtr<UDirectionalLightComponent> SunLight;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Sun", meta = (ClampMin = "0", ClampMax = "200000"))
	float NoonIntensity = 10.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Sun")
	float SunYaw = -35.0f;

	UFUNCTION(BlueprintPure, Category = "Sun")
	FRotator GetSunRotationForPhase(float Phase) const;

	UFUNCTION(BlueprintPure, Category = "Sun")
	float GetSunIntensityForPhase(float Phase) const;
};
