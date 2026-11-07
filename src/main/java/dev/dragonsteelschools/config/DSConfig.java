package dev.dragonsteelschools.config;

import net.minecraft.world.item.ArmorItem;
import net.minecraftforge.common.ForgeConfigSpec;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Common config. Defaults mirror Ice and Fire: Spellbooks 2.3.2's Dragon Priest armour and staves and Ice and
 * Fire 2.1.13's dragonsteel weapons; everything else is Tad's design.
 */
public final class DSConfig {
    public static final ForgeConfigSpec SPEC;

    public static final ForgeConfigSpec.ConfigValue<List<? extends String>> APEX_SPELLS;
    public static final ForgeConfigSpec.DoubleValue APEX_RANGE;
    public static final ForgeConfigSpec.DoubleValue CAULDRON_RANGE;

    public static final ForgeConfigSpec.ConfigValue<List<? extends Integer>> ARMOR_VALUES;
    public static final ForgeConfigSpec.DoubleValue ARMOR_MAX_MANA;
    public static final ForgeConfigSpec.DoubleValue ARMOR_SPELL_POWER;
    public static final ForgeConfigSpec.DoubleValue ARMOR_SCHOOL_POWER;

    public static final ForgeConfigSpec.DoubleValue DAWN_UNDEAD_BONUS;
    public static final ForgeConfigSpec.IntValue DAWN_HOLY_FIRE_SECONDS;
    public static final ForgeConfigSpec.DoubleValue HOLY_FIRE_DAMAGE;
    public static final ForgeConfigSpec.DoubleValue HOLY_FIRE_UNDEAD_MULTIPLIER;

    public static final ForgeConfigSpec.IntValue ELSEWHERE_RADIUS;
    public static final ForgeConfigSpec.IntValue ELSEWHERE_VERTICAL;
    public static final ForgeConfigSpec.DoubleValue ELSEWHERE_COOLDOWN_SECONDS;
    public static final ForgeConfigSpec.BooleanValue ELSEWHERE_SPELL_PROJECTILES;
    public static final ForgeConfigSpec.BooleanValue ELSEWHERE_OFFHAND;

    private static final List<Integer> DEFAULT_ARMOR = List.of(6, 9, 12, 6);
    private static volatile int generation;
    private static volatile Set<String> apexCache;

    static {
        ForgeConfigSpec.Builder b = new ForgeConfigSpec.Builder();

        b.push("forging");
        APEX_SPELLS = b.comment("Spells that finish dragonsteel in a dragon forge. Each spell forges its own school's",
                        "dragonsteel; a spell of a school without dragonsteel here does nothing. Defaults are Apex Arcana's.")
                .defineListAllowEmpty("apexSpells", List.of("grandsigil:heaven_gate", "grandsigil:reckoning",
                        "grandsigil:voidgrip", "grandsigil:dimension_cut"), o -> o instanceof String s && s.contains(":"));
        APEX_RANGE = b.comment("How far (blocks) an Apex caster may stand from the forge they are looking at.")
                .defineInRange("apexRange", 48.0, 4.0, 128.0);
        CAULDRON_RANGE = b.comment("How far (blocks) a caster may stand from the cauldron of dragon's breath.")
                .defineInRange("cauldronRange", 24.0, 2.0, 64.0);
        b.pop();

        b.push("armor");
        ARMOR_VALUES = b.comment("Armor points per piece [feet, legs, chest, head]. Spellbooks' Dragon Priest default: [6, 9, 12, 6].")
                .worldRestart()
                .defineList("armorValues", DEFAULT_ARMOR, o -> o instanceof Integer i && i >= 0);
        ARMOR_MAX_MANA = b.comment("Max mana per piece.").defineInRange("maxManaPerPiece", 150.0, 0.0, 10000.0);
        ARMOR_SPELL_POWER = b.comment("Spell power per piece (0.05 = +5%).").defineInRange("spellPowerPerPiece", 0.05, 0.0, 10.0);
        ARMOR_SCHOOL_POWER = b.comment("School power per piece (0.10 = +10%).").defineInRange("schoolPowerPerPiece", 0.10, 0.0, 10.0);
        b.pop();

        b.push("dawn");
        DAWN_UNDEAD_BONUS = b.comment("Extra melee damage Dawn deals to undead.").defineInRange("undeadBonus", 8.0, 0.0, 1000.0);
        DAWN_HOLY_FIRE_SECONDS = b.comment("Seconds of holy fire per hit.").defineInRange("holyFireSeconds", 15, 1, 600);
        HOLY_FIRE_DAMAGE = b.comment("Holy fire damage per second. It ignores armour, like ordinary fire, but water does not put it out.")
                .defineInRange("holyFireDamage", 1.0, 0.0, 100.0);
        HOLY_FIRE_UNDEAD_MULTIPLIER = b.comment("Holy fire damage multiplier against undead.")
                .defineInRange("holyFireUndeadMultiplier", 2.0, 0.0, 100.0);
        b.pop();

        b.push("elsewhere");
        ELSEWHERE_RADIUS = b.comment("Furthest horizontal distance (blocks) Elsewhere carries its wielder away from a projectile.")
                .defineInRange("radius", 16, 2, 64);
        ELSEWHERE_VERTICAL = b.comment("Furthest vertical distance (blocks) of that step.").defineInRange("vertical", 8, 1, 32);
        ELSEWHERE_COOLDOWN_SECONDS = b.comment("Cooldown after each dodge. 0 = none, like an enderman.")
                .defineInRange("cooldownSeconds", 0.0, 0.0, 600.0);
        ELSEWHERE_SPELL_PROJECTILES = b.comment("Also dodge spell projectiles and other thrown entities, not only arrows and tridents.")
                .define("dodgeSpellProjectiles", true);
        ELSEWHERE_OFFHAND = b.comment("Works from the offhand as well as the main hand.").define("worksInOffhand", true);
        b.pop();

        SPEC = b.build();
    }

    private DSConfig() {
    }

    /** Reads a value, falling back to its default before the config file has loaded. */
    public static <T> T get(ForgeConfigSpec.ConfigValue<T> value) {
        try {
            return value.get();
        } catch (IllegalStateException notLoaded) {
            return value.getDefault();
        }
    }

    public static void onReload() {
        generation++;
        apexCache = null;
    }

    /** Bumped on every config load or reload so cached attribute maps rebuild. */
    public static int generation() {
        return generation;
    }

    public static boolean isApex(String spellId) {
        Set<String> cache = apexCache;
        if (cache == null) {
            cache = new HashSet<>(get(APEX_SPELLS));
            apexCache = cache;
        }
        return cache.contains(spellId);
    }

    /** Armour points for a piece, from the [feet, legs, chest, head] list. */
    public static int armorPoints(ArmorItem.Type type) {
        List<? extends Integer> values = get(ARMOR_VALUES);
        if (values.size() != 4) {
            values = DEFAULT_ARMOR;
        }
        return values.get(type.getSlot().getIndex());
    }

    public static int seconds(ForgeConfigSpec.IntValue value) {
        return get(value) * 20;
    }

    public static int ticks(ForgeConfigSpec.DoubleValue seconds) {
        return (int) Math.round(get(seconds) * 20.0);
    }
}
