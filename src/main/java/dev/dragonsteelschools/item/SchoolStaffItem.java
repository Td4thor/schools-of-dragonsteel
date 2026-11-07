package dev.dragonsteelschools.item;

import dev.dragonsteelschools.school.SchoolSteel;
import io.redspace.ironsspellbooks.api.registry.AttributeRegistry;
import io.redspace.ironsspellbooks.item.weapons.AttributeContainer;
import io.redspace.ironsspellbooks.item.weapons.StaffItem;
import io.redspace.ironsspellbooks.item.weapons.StaffTier;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * School Dragon Priest staff. Same tier as Spellbooks' Crimson, Silver and Thunderous staves: 7 attack damage,
 * -3 attack speed, +25% school power and +20% cooldown reduction.
 */
public class SchoolStaffItem extends StaffItem {
    private final SchoolSteel school;

    public SchoolStaffItem(SchoolSteel school) {
        super(new Properties().stacksTo(1).fireResistant().rarity(Rarity.EPIC), tier(school));
        this.school = school;
    }

    public static StaffTier tier(SchoolSteel school) {
        return new StaffTier(7, -3,
                new AttributeContainer(school.schoolPower(), 0.25, AttributeModifier.Operation.MULTIPLY_BASE),
                new AttributeContainer(AttributeRegistry.COOLDOWN_REDUCTION, 0.20, AttributeModifier.Operation.MULTIPLY_BASE));
    }

    public SchoolSteel school() {
        return school;
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> lines, TooltipFlag flag) {
        lines.add(Component.translatable("item.dragonsteel_schools." + school.staffId() + ".lore").withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC));
        super.appendHoverText(stack, level, lines, flag);
    }
}
