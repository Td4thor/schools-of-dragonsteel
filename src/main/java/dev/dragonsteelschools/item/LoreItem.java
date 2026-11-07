package dev.dragonsteelschools.item;

import dev.dragonsteelschools.school.SchoolSteel;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/** A plain item with one line of lore naming its school. Used for the school bloods and ingots. */
public class LoreItem extends Item {
    private final String loreKey;
    private final SchoolSteel school;

    public LoreItem(Properties properties, String loreKey, SchoolSteel school) {
        super(properties);
        this.loreKey = loreKey;
        this.school = school;
    }

    public SchoolSteel school() {
        return school;
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> lines, TooltipFlag flag) {
        lines.add(Component.translatable(loreKey, school.displayName()).withStyle(ChatFormatting.GRAY));
    }
}
