using UnrealBuildTool;

public class NightFall : ModuleRules
{
	public NightFall(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"NetCore"
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
		});
	}
}
