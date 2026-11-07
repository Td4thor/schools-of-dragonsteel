package dev.dragonsteelschools.item;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.config.DSConfig;
import dev.dragonsteelschools.registry.ModItems;
import dev.dragonsteelschools.school.SchoolSteel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.crafting.Ingredient;

import java.util.EnumMap;
import java.util.Map;

/**
 * Mirrors Ice and Fire: Spellbooks 2.3.2's Dragon Priest material: durability multiplier 39 over vanilla's
 * 11/16/15/13 base, enchantability 15, netherite equip sound, toughness 6, knockback resistance 0.1. Armour points
 * come from the config, defaulting to Spellbooks' [6, 9, 12, 6].
 */
public final class SchoolArmorMaterial implements ArmorMaterial {
    private static final Map<ArmorItem.Type, Integer> BASE_DURABILITY = Map.of(
            ArmorItem.Type.HELMET, 11, ArmorItem.Type.CHESTPLATE, 16, ArmorItem.Type.LEGGINGS, 15, ArmorItem.Type.BOOTS, 13);
    public static final int DURABILITY_MULTIPLIER = 39;
    public static final float TOUGHNESS = 6.0F;
    public static final float KNOCKBACK_RESISTANCE = 0.1F;

    private static final Map<SchoolSteel, SchoolArmorMaterial> MATERIALS = new EnumMap<>(SchoolSteel.class);

    static {
        for (SchoolSteel school : SchoolSteel.values()) {
            MATERIALS.put(school, new SchoolArmorMaterial(school));
        }
    }

    private final SchoolSteel school;

    private SchoolArmorMaterial(SchoolSteel school) {
        this.school = school;
    }

    public static SchoolArmorMaterial of(SchoolSteel school) {
        return MATERIALS.get(school);
    }

    @Override
    public int getDurabilityForType(ArmorItem.Type type) {
        return BASE_DURABILITY.get(type) * DURABILITY_MULTIPLIER;
    }

    @Override
    public int getDefenseForType(ArmorItem.Type type) {
        return DSConfig.armorPoints(type);
    }

    @Override
    public int getEnchantmentValue() {
        return 15;
    }

    @Override
    public SoundEvent getEquipSound() {
        return SoundEvents.ARMOR_EQUIP_NETHERITE;
    }

    @Override
    public Ingredient getRepairIngredient() {
        return Ingredient.of(ModItems.INGOT.get(school).get());
    }

    @Override
    public String getName() {
        return DragonsteelSchools.MODID + ":" + school.id() + "_dragonsteel";
    }

    @Override
    public float getToughness() {
        return TOUGHNESS;
    }

    @Override
    public float getKnockbackResistance() {
        return KNOCKBACK_RESISTANCE;
    }
}
