package dev.dragonsteelschools.compat.jei;

import dev.dragonsteelschools.config.DSConfig;
import dev.dragonsteelschools.registry.ModItems;
import dev.dragonsteelschools.school.SchoolSteel;
import io.redspace.ironsspellbooks.api.spells.AbstractSpell;
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
import net.minecraft.world.item.Items;

import java.util.List;

/**
 * School Dragon Blood: Dragon's Breath in a cauldron, a spell of the school cast at it, the school's blood drawn out
 * with glass bottles. The spell icon cycles through the school's spells, any of which will do.
 */
final class BloodCategory implements IRecipeCategory<BloodRecipe> {
    static final int WIDTH = 160;
    static final int HEIGHT = 84;
    private static final int TEXT = 0x404040;
    private static final int SPELL_X = 56;
    private static final int SPELL_Y = 7;

    private final IDrawableStatic background;
    private final IDrawable icon;
    private final IDrawableStatic arrow;
    private final IDrawableStatic slot;
    private final IDrawableStatic outputSlot;

    BloodCategory(IGuiHelper gui) {
        this.background = gui.createBlankDrawable(WIDTH, HEIGHT);
        this.icon = gui.createDrawableItemStack(new ItemStack(ModItems.BLOOD.get(SchoolSteel.HOLY).get()));
        this.arrow = gui.getRecipeArrow();
        this.slot = gui.getSlotDrawable();
        this.outputSlot = gui.getOutputSlot();
    }

    @Override
    public RecipeType<BloodRecipe> getRecipeType() {
        return DragonsteelJeiPlugin.BLOOD;
    }

    @Override
    public Component getTitle() {
        return Component.translatable("jei.dragonsteel_schools.blood");
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
    public void setRecipe(IRecipeLayoutBuilder builder, BloodRecipe recipe, IFocusGroup focuses) {
        builder.addSlot(RecipeIngredientRole.INPUT, 4, 7).addItemStack(new ItemStack(Items.DRAGON_BREATH)).setBackground(slot, -1, -1);
        builder.addSlot(RecipeIngredientRole.CATALYST, 30, 7).addItemStack(new ItemStack(Items.CAULDRON)).setBackground(slot, -1, -1);
        builder.addSlot(RecipeIngredientRole.OUTPUT, 116, 7).addItemStack(recipe.blood()).setBackground(outputSlot, -5, -5);
    }

    @Override
    public void draw(BloodRecipe recipe, IRecipeSlotsView slots, GuiGraphics graphics, double mouseX, double mouseY) {
        Font font = Minecraft.getInstance().font;
        AbstractSpell spell = shown(recipe);
        slot.draw(graphics, SPELL_X - 1, SPELL_Y - 1);
        if (spell != null) {
            JeiDraw.spellIcon(graphics, spell, SPELL_X, SPELL_Y);
        }
        graphics.drawString(font, "+", 22, 11, TEXT, false);
        graphics.drawString(font, "+", 48, 11, TEXT, false);
        arrow.draw(graphics, 82, 7);
        JeiDraw.wrapped(graphics, font, Component.translatable("jei.dragonsteel_schools.blood.how", recipe.school().displayName(),
                DragonsteelJeiPlugin.fmt(DSConfig.get(DSConfig.CAULDRON_RANGE))), 2, 32, WIDTH - 4, TEXT);
    }

    @Override
    @SuppressWarnings("removal")
    public List<Component> getTooltipStrings(BloodRecipe recipe, IRecipeSlotsView slots, double mouseX, double mouseY) {
        AbstractSpell spell = shown(recipe);
        if (spell == null || !JeiDraw.inside(mouseX, mouseY, SPELL_X, SPELL_Y, 16)) {
            return List.of();
        }
        return List.of(Component.translatable("jei.dragonsteel_schools.blood.any", recipe.school().displayName()),
                Component.translatable("jei.dragonsteel_schools.blood.example", Component.translatable(spell.getComponentId())));
    }

    /** The spell icon on show this second. */
    private static AbstractSpell shown(BloodRecipe recipe) {
        List<AbstractSpell> spells = recipe.spells();
        return spells.isEmpty() ? null : spells.get((int) ((System.currentTimeMillis() / 1000L) % spells.size()));
    }
}
