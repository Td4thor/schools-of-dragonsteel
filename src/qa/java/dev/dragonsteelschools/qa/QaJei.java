package dev.dragonsteelschools.qa;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.compat.jei.DragonsteelJeiPlugin;
import mezz.jei.api.constants.RecipeTypes;
import mezz.jei.api.constants.VanillaTypes;
import mezz.jei.api.recipe.RecipeType;
import mezz.jei.api.recipe.category.IRecipeCategory;
import mezz.jei.api.recipe.vanilla.IJeiIngredientInfoRecipe;
import mezz.jei.api.runtime.IJeiRuntime;
import net.minecraft.world.item.Item;

import java.util.List;

/** Opens the mod's JEI pages for the QA screenshots. Only called when JEI is loaded. */
final class QaJei {
    private QaJei() {
    }

    static void showType(boolean finishing) {
        IJeiRuntime runtime = DragonsteelJeiPlugin.runtime();
        if (runtime == null) {
            DragonsteelSchools.LOG.warn("[DragonsteelSchools/qa] JEI runtime not available");
            return;
        }
        RecipeType<?> type = finishing ? DragonsteelJeiPlugin.finishingType() : DragonsteelJeiPlugin.bloodType();
        DragonsteelSchools.LOG.info("[DragonsteelSchools/qa] JEI {}: {} recipes", type.getUid(),
                runtime.getRecipeManager().createRecipeLookup(type).get().count());
        runtime.getRecipesGui().showTypes(List.of(type));
    }

    /** The JEI information page of one item. */
    static void showInfo(Item item) {
        IJeiRuntime runtime = DragonsteelJeiPlugin.runtime();
        if (runtime == null) {
            DragonsteelSchools.LOG.warn("[DragonsteelSchools/qa] JEI runtime not available");
            return;
        }
        IRecipeCategory<IJeiIngredientInfoRecipe> category = runtime.getRecipeManager().getRecipeCategory(RecipeTypes.INFORMATION);
        List<IJeiIngredientInfoRecipe> pages = runtime.getRecipeManager().createRecipeLookup(RecipeTypes.INFORMATION).get()
                .filter(page -> page.getIngredients().stream()
                        .anyMatch(ingredient -> ingredient.getIngredient(VanillaTypes.ITEM_STACK).map(stack -> stack.is(item)).orElse(false)))
                .toList();
        DragonsteelSchools.LOG.info("[DragonsteelSchools/qa] JEI information for {}: {} pages", item, pages.size());
        if (!pages.isEmpty()) {
            runtime.getRecipesGui().showRecipes(category, pages, List.of());
        }
    }
}
