package dev.dragonsteelschools.item;

import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.Multimap;
import dev.dragonsteelschools.config.DSConfig;
import dev.dragonsteelschools.school.SchoolSteel;
import io.redspace.ironsspellbooks.api.registry.AttributeRegistry;
import io.redspace.ironsspellbooks.api.spells.IPresetSpellContainer;
import io.redspace.ironsspellbooks.api.spells.ISpellContainer;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;
import software.bernie.geckolib.animatable.GeoItem;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.EnumMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Consumer;

/**
 * School mage plate. Per piece, the same numbers as Spellbooks' Dragon Priest regalia: armour (config), toughness 6,
 * knockback resistance 0.1, +150 max mana, +5% spell power and +10% power for its own school. The chestplate holds
 * one imbued spell. Rendered by Iron's GeckoLib armour renderer (client only, see PlateArmorClientExtensions).
 */
public class SchoolPlateArmorItem extends ArmorItem implements GeoItem, IPresetSpellContainer {
    private static final Map<ArmorItem.Type, UUID> SLOT_UUIDS = new EnumMap<>(Map.of(
            ArmorItem.Type.HELMET, UUID.fromString("9d4c3e1a-58b2-4f37-a1c6-3e0f8b7d2a01"),
            ArmorItem.Type.CHESTPLATE, UUID.fromString("9d4c3e1a-58b2-4f37-a1c6-3e0f8b7d2a02"),
            ArmorItem.Type.LEGGINGS, UUID.fromString("9d4c3e1a-58b2-4f37-a1c6-3e0f8b7d2a03"),
            ArmorItem.Type.BOOTS, UUID.fromString("9d4c3e1a-58b2-4f37-a1c6-3e0f8b7d2a04")));

    private final SchoolSteel school;
    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private Multimap<Attribute, AttributeModifier> modifiers;
    private int modifiersGeneration = -1;

    public SchoolPlateArmorItem(SchoolSteel school, ArmorItem.Type type, Properties properties) {
        super(SchoolArmorMaterial.of(school), type, properties);
        this.school = school;
    }

    public SchoolSteel school() {
        return school;
    }

    @Override
    public Multimap<Attribute, AttributeModifier> getDefaultAttributeModifiers(EquipmentSlot slot) {
        if (slot != this.type.getSlot()) {
            return ImmutableMultimap.of();
        }
        if (modifiers == null || modifiersGeneration != DSConfig.generation()) {
            modifiers = buildModifiers();
            modifiersGeneration = DSConfig.generation();
        }
        return modifiers;
    }

    private Multimap<Attribute, AttributeModifier> buildModifiers() {
        UUID id = SLOT_UUIDS.get(this.type);
        ImmutableMultimap.Builder<Attribute, AttributeModifier> builder = ImmutableMultimap.builder();
        builder.put(Attributes.ARMOR, new AttributeModifier(id, "Armor modifier", DSConfig.armorPoints(this.type), AttributeModifier.Operation.ADDITION));
        builder.put(Attributes.ARMOR_TOUGHNESS, new AttributeModifier(id, "Armor toughness", SchoolArmorMaterial.TOUGHNESS, AttributeModifier.Operation.ADDITION));
        builder.put(Attributes.KNOCKBACK_RESISTANCE, new AttributeModifier(id, "Armor knockback resistance", SchoolArmorMaterial.KNOCKBACK_RESISTANCE, AttributeModifier.Operation.ADDITION));
        builder.put(AttributeRegistry.MAX_MANA.get(), new AttributeModifier(id, "Armor max mana", DSConfig.get(DSConfig.ARMOR_MAX_MANA), AttributeModifier.Operation.ADDITION));
        builder.put(AttributeRegistry.SPELL_POWER.get(), new AttributeModifier(id, "Armor spell power", DSConfig.get(DSConfig.ARMOR_SPELL_POWER), AttributeModifier.Operation.MULTIPLY_BASE));
        builder.put(school.schoolPower().get(), new AttributeModifier(id, "Armor school power", DSConfig.get(DSConfig.ARMOR_SCHOOL_POWER), AttributeModifier.Operation.MULTIPLY_BASE));
        return builder.build();
    }

    @Override
    public void initializeSpellContainer(ItemStack stack) {
        if (stack != null && this.type == ArmorItem.Type.CHESTPLATE && !ISpellContainer.isSpellContainer(stack)) {
            ISpellContainer.set(stack, ISpellContainer.create(1, true, true));
        }
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        // Static plate: GeckoLib's armour renderer follows the wearer's limbs on its own.
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }

    @Override
    public void initializeClient(Consumer<IClientItemExtensions> consumer) {
        // Runs inside the Item constructor, before this.school is set: pass nothing from this object's fields.
        consumer.accept(new dev.dragonsteelschools.client.PlateArmorClientExtensions());
    }
}
