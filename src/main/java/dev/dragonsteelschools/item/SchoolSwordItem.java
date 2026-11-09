package dev.dragonsteelschools.item;

import dev.dragonsteelschools.combat.SwordPowers;
import dev.dragonsteelschools.school.SchoolSteel;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * A school's named dragonsteel sword (Thirst, Covenant, Briar, Hush). Its power lives in {@link SwordPowers};
 * the tooltip shows the power with its configured numbers.
 */
public class SchoolSwordItem extends SwordItem {
    private final SchoolSteel school;

    public SchoolSwordItem(SchoolSteel school, Tier tier, int attackDamage, float attackSpeed, Properties properties) {
        super(tier, attackDamage, attackSpeed, properties);
        this.school = school;
    }

    public SchoolSteel school() {
        return school;
    }

    @Override
    public boolean hurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
        if (!target.level().isClientSide) {
            SwordPowers.onHit(school, target, attacker);
        }
        return super.hurtEnemy(stack, target, attacker);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> lines, TooltipFlag flag) {
        String key = "item.dragonsteel_schools." + school.swordId();
        lines.add(Component.translatable(key + ".power", SwordPowers.tooltipArgs(school)).withStyle(style -> style.withColor(school.primaryColor())));
    }
}
