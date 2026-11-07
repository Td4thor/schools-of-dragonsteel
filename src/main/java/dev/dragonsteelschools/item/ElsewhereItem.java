package dev.dragonsteelschools.item;

import dev.dragonsteelschools.config.DSConfig;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/** Elsewhere, the Ender dragonsteel sword. While held, its wielder steps away from projectiles (ElsewhereDodge). */
public class ElsewhereItem extends SwordItem {
    public ElsewhereItem(Tier tier, int attackDamage, float attackSpeed, Properties properties) {
        super(tier, attackDamage, attackSpeed, properties);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> lines, TooltipFlag flag) {
        lines.add(Component.translatable("item.dragonsteel_schools.elsewhere.lore").withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC));
        lines.add(Component.translatable(DSConfig.get(DSConfig.ELSEWHERE_SPELL_PROJECTILES)
                ? "item.dragonsteel_schools.elsewhere.dodge_all" : "item.dragonsteel_schools.elsewhere.dodge_arrows")
                .withStyle(ChatFormatting.LIGHT_PURPLE));
    }
}
