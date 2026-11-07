package dev.dragonsteelschools.school;

import dev.dragonsteelschools.DragonsteelSchools;
import io.redspace.ironsspellbooks.api.registry.AttributeRegistry;
import io.redspace.ironsspellbooks.api.registry.SchoolRegistry;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.ai.attributes.Attribute;

import java.util.Arrays;
import java.util.Optional;
import java.util.function.Supplier;

/**
 * One entry per spell school that gets its own dragonsteel. Fire, Ice and Lightning already have Ice and Fire's.
 * Everything school-specific in the code reads it from here; a new school is one constant plus its art and data.
 */
public enum SchoolSteel {
    HOLY("holy", SchoolRegistry.HOLY_RESOURCE, "dawn", "gilded_dragon_priest_staff", 0xFFE9A6, 0xFFFFFF,
            () -> AttributeRegistry.HOLY_SPELL_POWER.get(), () -> SoundEvents.BEACON_ACTIVATE, () -> ParticleTypes.END_ROD, 6, 3),
    ENDER("ender", SchoolRegistry.ENDER_RESOURCE, "elsewhere", "umbral_dragon_priest_staff", 0xA45CFF, 0x2A0E4A,
            () -> AttributeRegistry.ENDER_SPELL_POWER.get(), () -> SoundEvents.END_PORTAL_FRAME_FILL, () -> ParticleTypes.REVERSE_PORTAL, 2, 1),
    BLOOD("blood", SchoolRegistry.BLOOD_RESOURCE, "thirst", "sanguine_dragon_priest_staff", 0xC21A2B, 0x3A0509,
            () -> AttributeRegistry.BLOOD_SPELL_POWER.get(), () -> SoundEvents.RESPAWN_ANCHOR_CHARGE, () -> ParticleTypes.CRIMSON_SPORE, 2, 1),
    EVOCATION("evocation", SchoolRegistry.EVOCATION_RESOURCE, "covenant", "emerald_dragon_priest_staff", 0x3DDB7A, 0x4A2B17,
            () -> AttributeRegistry.EVOCATION_SPELL_POWER.get(), () -> SoundEvents.EVOKER_CAST_SPELL, () -> ParticleTypes.HAPPY_VILLAGER, 3, 2),
    NATURE("nature", SchoolRegistry.NATURE_RESOURCE, "briar", "verdant_dragon_priest_staff", 0x6FCF3A, 0x23301B,
            () -> AttributeRegistry.NATURE_SPELL_POWER.get(), () -> SoundEvents.BONE_MEAL_USE, () -> ParticleTypes.SPORE_BLOSSOM_AIR, 2, 1),
    ELDRITCH("eldritch", SchoolRegistry.ELDRITCH_RESOURCE, "hush", "abyssal_dragon_priest_staff", 0x29DFEB, 0x061A20,
            () -> AttributeRegistry.ELDRITCH_SPELL_POWER.get(), () -> SoundEvents.SCULK_CATALYST_BLOOM, () -> ParticleTypes.SCULK_SOUL, 2, 2);

    private final String id;
    private final ResourceLocation schoolId;
    private final String swordId;
    private final String staffId;
    private final int primaryColor;
    private final int secondaryColor;
    private final Supplier<Attribute> schoolPower;
    private final Supplier<SoundEvent> forgeSound;
    private final Supplier<ParticleOptions> particle;
    private final int cauldronLightBase;
    private final int cauldronLightPerLevel;

    SchoolSteel(String id, ResourceLocation schoolId, String swordId, String staffId, int primaryColor, int secondaryColor,
                Supplier<Attribute> schoolPower, Supplier<SoundEvent> forgeSound, Supplier<ParticleOptions> particle,
                int cauldronLightBase, int cauldronLightPerLevel) {
        this.id = id;
        this.schoolId = schoolId;
        this.swordId = swordId;
        this.staffId = staffId;
        this.primaryColor = primaryColor;
        this.secondaryColor = secondaryColor;
        this.schoolPower = schoolPower;
        this.forgeSound = forgeSound;
        this.particle = particle;
        this.cauldronLightBase = cauldronLightBase;
        this.cauldronLightPerLevel = cauldronLightPerLevel;
    }

    public String id() {
        return id;
    }

    /** Iron's Spells school id, e.g. {@code irons_spellbooks:holy}. */
    public ResourceLocation schoolId() {
        return schoolId;
    }

    public String swordId() {
        return swordId;
    }

    public String staffId() {
        return staffId;
    }

    /** The school's colour (dust particles, tooltips). */
    public int primaryColor() {
        return primaryColor;
    }

    public int secondaryColor() {
        return secondaryColor;
    }

    public Supplier<Attribute> schoolPower() {
        return schoolPower;
    }

    public SoundEvent forgeSound() {
        return forgeSound.get();
    }

    /** The school's signature particle (cauldron, attunement, forging). */
    public ParticleOptions particle() {
        return particle.get();
    }

    /** Light level of a cauldron of this school's blood at the given fill level (1 to 3). */
    public int cauldronLight(int level) {
        return Math.min(15, cauldronLightBase + cauldronLightPerLevel * level);
    }

    public Component displayName() {
        return Component.translatable("school." + DragonsteelSchools.MODID + "." + id);
    }

    public static Optional<SchoolSteel> bySchool(ResourceLocation school) {
        return Arrays.stream(values()).filter(s -> s.schoolId.equals(school)).findFirst();
    }

    public static Optional<SchoolSteel> byId(String id) {
        return Arrays.stream(values()).filter(s -> s.id.equals(id)).findFirst();
    }
}
