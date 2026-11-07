package dev.dragonsteelschools.item;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.registry.ModItems;
import dev.dragonsteelschools.school.SchoolSteel;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.Tiers;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.level.block.Block;
import net.minecraftforge.common.ForgeTier;
import net.minecraftforge.common.TierSortingRegistry;

import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/**
 * Dragonsteel tiers. Same numbers as Ice and Fire 2.1.13's DragonSteelTier: level 4, 8000 uses, mining speed 10,
 * attack bonus 21, enchantability 10, sorted after netherite.
 */
public final class SchoolTiers {
    public static final TagKey<Block> NEEDS_SCHOOL_DRAGONSTEEL =
            BlockTags.create(new ResourceLocation(DragonsteelSchools.MODID, "needs_school_dragonsteel"));

    private static final Map<SchoolSteel, Tier> TIERS = new EnumMap<>(SchoolSteel.class);

    static {
        for (SchoolSteel school : SchoolSteel.values()) {
            Tier tier = new ForgeTier(4, 8000, 10.0F, 21.0F, 10, NEEDS_SCHOOL_DRAGONSTEEL,
                    () -> Ingredient.of(ModItems.INGOT.get(school).get()));
            TierSortingRegistry.registerTier(tier, new ResourceLocation(DragonsteelSchools.MODID, school.id() + "_dragonsteel"),
                    List.of(Tiers.NETHERITE), List.of());
            TIERS.put(school, tier);
        }
    }

    private SchoolTiers() {
    }

    public static Tier of(SchoolSteel school) {
        return TIERS.get(school);
    }
}
