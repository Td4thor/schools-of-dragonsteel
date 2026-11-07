package dev.dragonsteelschools.school;

import dev.dragonsteelschools.DragonsteelSchools;
import io.redspace.ironsspellbooks.api.registry.AttributeRegistry;
import io.redspace.ironsspellbooks.api.registry.SchoolRegistry;
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
 * Adding Blood, Evocation, Nature or Eldritch later means one constant here plus its art and data files.
 */
public enum SchoolSteel {
    HOLY("holy", SchoolRegistry.HOLY_RESOURCE, "dawn", "gilded_dragon_priest_staff", 0xFFE9A6, 0xFFFFFF),
    ENDER("ender", SchoolRegistry.ENDER_RESOURCE, "elsewhere", "umbral_dragon_priest_staff", 0xA45CFF, 0x2A0E4A);

    private final String id;
    private final ResourceLocation schoolId;
    private final String swordId;
    private final String staffId;
    private final int primaryColor;
    private final int secondaryColor;

    SchoolSteel(String id, ResourceLocation schoolId, String swordId, String staffId, int primaryColor, int secondaryColor) {
        this.id = id;
        this.schoolId = schoolId;
        this.swordId = swordId;
        this.staffId = staffId;
        this.primaryColor = primaryColor;
        this.secondaryColor = secondaryColor;
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

    public int primaryColor() {
        return primaryColor;
    }

    public int secondaryColor() {
        return secondaryColor;
    }

    public Supplier<Attribute> schoolPower() {
        return switch (this) {
            case HOLY -> AttributeRegistry.HOLY_SPELL_POWER;
            case ENDER -> AttributeRegistry.ENDER_SPELL_POWER;
        };
    }

    public SoundEvent forgeSound() {
        return switch (this) {
            case HOLY -> SoundEvents.BEACON_ACTIVATE;
            case ENDER -> SoundEvents.END_PORTAL_FRAME_FILL;
        };
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
