package dev.dragonsteelschools.item;

import dev.dragonsteelschools.config.DSConfig;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;
import org.jetbrains.annotations.Nullable;

import java.util.List;
import java.util.function.Consumer;

/**
 * Elsewhere, the Ender dragonsteel sword. While held, its wielder steps away from projectiles (ElsewhereDodge).
 * In the hand its three lengths drift apart, fly apart on a swing and scatter on a dodge (client.ElsewhereRenderer).
 */
public class ElsewhereItem extends SwordItem {
    public ElsewhereItem(Tier tier, int attackDamage, float attackSpeed, Properties properties) {
        super(tier, attackDamage, attackSpeed, properties);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> lines, TooltipFlag flag) {
        lines.add(Component.translatable(DSConfig.get(DSConfig.ELSEWHERE_SPELL_PROJECTILES)
                ? "item.dragonsteel_schools.elsewhere.dodge_all" : "item.dragonsteel_schools.elsewhere.dodge_arrows")
                .withStyle(ChatFormatting.LIGHT_PURPLE));
    }

    @Override
    public void initializeClient(Consumer<IClientItemExtensions> consumer) {
        // Runs inside the Item constructor and only on the client: pass nothing from this object's fields.
        consumer.accept(new dev.dragonsteelschools.client.ElsewhereClientExtensions());
    }
}
