package dev.dragonsteelschools.registry;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.combat.HolyFireEffect;
import dev.dragonsteelschools.forge.ApexForgingRecipe;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.Level;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

/** Effects, recipe types, damage types and the creative tab. */
public final class ModRegistries {
    public static final DeferredRegister<MobEffect> EFFECTS = DeferredRegister.create(ForgeRegistries.MOB_EFFECTS, DragonsteelSchools.MODID);
    public static final DeferredRegister<RecipeType<?>> RECIPE_TYPES = DeferredRegister.create(ForgeRegistries.RECIPE_TYPES, DragonsteelSchools.MODID);
    public static final DeferredRegister<RecipeSerializer<?>> RECIPE_SERIALIZERS = DeferredRegister.create(ForgeRegistries.RECIPE_SERIALIZERS, DragonsteelSchools.MODID);
    public static final DeferredRegister<CreativeModeTab> TABS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, DragonsteelSchools.MODID);

    public static final RegistryObject<MobEffect> HOLY_FIRE = EFFECTS.register("holy_fire", HolyFireEffect::new);

    public static final RegistryObject<RecipeType<ApexForgingRecipe>> APEX_FORGING = RECIPE_TYPES.register("apex_forging",
            () -> RecipeType.simple(new ResourceLocation(DragonsteelSchools.MODID, "apex_forging")));
    public static final RegistryObject<RecipeSerializer<ApexForgingRecipe>> APEX_FORGING_SERIALIZER =
            RECIPE_SERIALIZERS.register("apex_forging", ApexForgingRecipe.Serializer::new);

    public static final ResourceKey<DamageType> HOLY_FIRE_DAMAGE =
            ResourceKey.create(Registries.DAMAGE_TYPE, new ResourceLocation(DragonsteelSchools.MODID, "holy_fire"));

    public static final RegistryObject<CreativeModeTab> TAB = TABS.register("main", () -> CreativeModeTab.builder()
            .title(Component.translatable("itemGroup.dragonsteel_schools"))
            .icon(() -> new ItemStack(ModItems.SWORD.get(dev.dragonsteelschools.school.SchoolSteel.HOLY).get()))
            .displayItems((params, output) -> ModItems.ORDERED.forEach(item -> output.accept(item.get())))
            .build());

    private ModRegistries() {
    }

    public static DamageSource holyFire(Level level) {
        return new DamageSource(level.registryAccess().registryOrThrow(Registries.DAMAGE_TYPE).getHolderOrThrow(HOLY_FIRE_DAMAGE));
    }
}
