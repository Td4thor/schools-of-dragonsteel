package dev.dragonsteelschools.compat.jei;

import dev.dragonsteelschools.config.DSConfig;
import dev.dragonsteelschools.forge.FinishingRule;
import dev.dragonsteelschools.forge.ForgeBatchMath;
import dev.dragonsteelschools.registry.ModItems;
import dev.dragonsteelschools.school.SchoolSteel;
import mezz.jei.api.gui.builder.IRecipeLayoutBuilder;
import mezz.jei.api.gui.drawable.IDrawable;
import mezz.jei.api.gui.drawable.IDrawableStatic;
import mezz.jei.api.gui.ingredient.IRecipeSlotsView;
import mezz.jei.api.helpers.IGuiHelper;
import mezz.jei.api.recipe.IFocusGroup;
import mezz.jei.api.recipe.RecipeIngredientRole;
import mezz.jei.api.recipe.RecipeType;
import mezz.jei.api.recipe.category.IRecipeCategory;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.List;

/**
 * Dragonsteel Finishing: one page per spell that finishes a school's tempered steel at a dragon forge. The spell's
 * icon and name head the page, then the steel going in and the ingot coming out, then how to cast it.
 */
final class FinishingCategory implements IRecipeCategory<FinishingRecipe> {
    static final int WIDTH = 160;
    static final int HEIGHT = 90;
    private static final int TEXT = 0x404040;
    private static final int MUTED = 0x5A5A5A;
    private static final int WARN = 0xA02020;

    private final IDrawableStatic background;
    private final IDrawable icon;
    private final IDrawableStatic arrow;
    private final IDrawableStatic slot;
    private final IDrawableStatic outputSlot;

    FinishingCategory(IGuiHelper gui) {
        this.background = gui.createBlankDrawable(WIDTH, HEIGHT);
        this.icon = gui.createDrawableItemStack(new ItemStack(ModItems.INGOT.get(SchoolSteel.HOLY).get()));
        this.arrow = gui.getRecipeArrow();
        this.slot = gui.getSlotDrawable();
        this.outputSlot = gui.getOutputSlot();
    }

    @Override
    public RecipeType<FinishingRecipe> getRecipeType() {
        return DragonsteelJeiPlugin.FINISHING;
    }

    @Override
    public Component getTitle() {
        return Component.translatable("jei.dragonsteel_schools.finishing");
    }

    @Override
    @SuppressWarnings("removal")
    public IDrawable getBackground() {
        return background;
    }

    @Override
    public int getWidth() {
        return WIDTH;
    }

    @Override
    public int getHeight() {
        return HEIGHT;
    }

    @Override
    public IDrawable getIcon() {
        return icon;
    }

    @Override
    public void setRecipe(IRecipeLayoutBuilder builder, FinishingRecipe recipe, IFocusGroup focuses) {
        builder.addSlot(RecipeIngredientRole.INPUT, 38, 27).addItemStack(recipe.tempered()).setBackground(slot, -1, -1);
        builder.addSlot(RecipeIngredientRole.OUTPUT, 104, 27).addItemStack(recipe.ingot()).setBackground(outputSlot, -5, -5);
    }

    @Override
    public void draw(FinishingRecipe recipe, IRecipeSlotsView slots, GuiGraphics graphics, double mouseX, double mouseY) {
        Font font = Minecraft.getInstance().font;
        JeiDraw.spellIcon(graphics, recipe.spell(), 2, 2);
        graphics.drawString(font, Component.translatable(recipe.spell().getComponentId()), 22, 2, TEXT, false);
        Component level = recipe.apex()
                ? Component.translatable("jei.dragonsteel_schools.finishing.apex")
                : Component.translatable("jei.dragonsteel_schools.finishing.legendary", recipe.minLevel());
        graphics.drawString(font, level, 22, 12, MUTED, false);
        arrow.draw(graphics, 68, 27);
        Component how = !recipe.apex() && FinishingRule.forTooltip() == FinishingRule.APEX_ONLY
                ? Component.translatable("jei.dragonsteel_schools.finishing.disabled")
                : Component.translatable("jei.dragonsteel_schools.finishing.how",
                DragonsteelJeiPlugin.fmt(DSConfig.get(DSConfig.FINISHING_RANGE)), ForgeBatchMath.MAX_PER_CAST);
        int color = !recipe.apex() && FinishingRule.forTooltip() == FinishingRule.APEX_ONLY ? WARN : TEXT;
        JeiDraw.wrapped(graphics, font, how, 2, 50, WIDTH - 4, color);
    }

    @Override
    @SuppressWarnings("removal")
    public List<Component> getTooltipStrings(FinishingRecipe recipe, IRecipeSlotsView slots, double mouseX, double mouseY) {
        if (!JeiDraw.inside(mouseX, mouseY, 2, 2, 16)) {
            return List.of();
        }
        List<Component> lines = new ArrayList<>();
        lines.add(Component.translatable(recipe.spell().getComponentId()));
        lines.add(Component.translatable("jei.dragonsteel_schools.spell_school", recipe.school().displayName()));
        lines.add(recipe.apex()
                ? Component.translatable("jei.dragonsteel_schools.finishing.apex.tip")
                : Component.translatable("jei.dragonsteel_schools.finishing.legendary.tip", recipe.minLevel(), recipe.spell().getMaxLevel()));
        return lines;
    }
}
