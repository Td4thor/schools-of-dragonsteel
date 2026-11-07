package dev.dragonsteelschools.item;

import dev.dragonsteelschools.combat.HolyFire;
import dev.dragonsteelschools.config.DSConfig;
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

/** Dawn, the Holy dragonsteel sword. Sets what it strikes alight with holy fire; undead take extra (DawnEvents). */
public class DawnItem extends SwordItem {
    public DawnItem(Tier tier, int attackDamage, float attackSpeed, Properties properties) {
        super(tier, attackDamage, attackSpeed, properties);
    }

    @Override
    public boolean hurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
        if (!target.level().isClientSide) {
            HolyFire.ignite(target, attacker, DSConfig.seconds(DSConfig.DAWN_HOLY_FIRE_SECONDS));
        }
        return super.hurtEnemy(stack, target, attacker);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> lines, TooltipFlag flag) {
        lines.add(Component.translatable("item.dragonsteel_schools.dawn.lore").withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC));
        lines.add(Component.translatable("item.dragonsteel_schools.dawn.holy_fire",
                DSConfig.get(DSConfig.DAWN_HOLY_FIRE_SECONDS)).withStyle(ChatFormatting.GOLD));
        lines.add(Component.translatable("item.dragonsteel_schools.dawn.undead",
                fmt(DSConfig.get(DSConfig.DAWN_UNDEAD_BONUS))).withStyle(ChatFormatting.GOLD));
    }

    static String fmt(double value) {
        return value == Math.rint(value) ? Integer.toString((int) value) : String.format(java.util.Locale.ROOT, "%.1f", value);
    }
}
