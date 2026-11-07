package dev.dragonsteelschools.forge;

import com.google.gson.JsonObject;
import com.google.gson.JsonSyntaxException;
import dev.dragonsteelschools.registry.ModRegistries;
import dev.dragonsteelschools.school.SchoolSteel;
import net.minecraft.core.NonNullList;
import net.minecraft.core.RegistryAccess;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.GsonHelper;
import net.minecraft.world.Container;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.crafting.ShapedRecipe;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

/**
 * What a school's Apex spell finishes in a dragon forge: each {@code input} (breath-tempered steel) in the forge's
 * output or input slot becomes {@code result}. JSON type {@code dragonsteel_schools:apex_forging}.
 */
public record ApexForgingRecipe(ResourceLocation id, SchoolSteel school, Ingredient input, ItemStack result)
        implements Recipe<Container> {

    public boolean accepts(ItemStack stack) {
        return !stack.isEmpty() && input.test(stack);
    }

    @Override
    public boolean matches(Container container, Level level) {
        return container.getContainerSize() > DragonForges.SLOT_OUTPUT
                && (accepts(container.getItem(DragonForges.SLOT_OUTPUT)) || accepts(container.getItem(DragonForges.SLOT_INPUT)));
    }

    @Override
    public ItemStack assemble(Container container, RegistryAccess access) {
        return result.copy();
    }

    @Override
    public boolean canCraftInDimensions(int width, int height) {
        return true;
    }

    @Override
    public ItemStack getResultItem(RegistryAccess access) {
        return result;
    }

    @Override
    public NonNullList<Ingredient> getIngredients() {
        return NonNullList.of(Ingredient.EMPTY, input);
    }

    @Override
    public ResourceLocation getId() {
        return id;
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return ModRegistries.APEX_FORGING_SERIALIZER.get();
    }

    @Override
    public RecipeType<?> getType() {
        return ModRegistries.APEX_FORGING.get();
    }

    @Override
    public boolean isSpecial() {
        return true;
    }

    public static final class Serializer implements RecipeSerializer<ApexForgingRecipe> {
        @Override
        public ApexForgingRecipe fromJson(ResourceLocation id, JsonObject json) {
            String schoolId = GsonHelper.getAsString(json, "school");
            SchoolSteel school = SchoolSteel.byId(schoolId)
                    .orElseThrow(() -> new JsonSyntaxException("Unknown dragonsteel school '" + schoolId + "' in " + id));
            Ingredient input = Ingredient.fromJson(GsonHelper.getNonNull(json, "input"));
            ItemStack result = ShapedRecipe.itemStackFromJson(GsonHelper.getAsJsonObject(json, "result"));
            return new ApexForgingRecipe(id, school, input, result);
        }

        @Override
        public @Nullable ApexForgingRecipe fromNetwork(ResourceLocation id, FriendlyByteBuf buf) {
            SchoolSteel school = buf.readEnum(SchoolSteel.class);
            Ingredient input = Ingredient.fromNetwork(buf);
            ItemStack result = buf.readItem();
            return new ApexForgingRecipe(id, school, input, result);
        }

        @Override
        public void toNetwork(FriendlyByteBuf buf, ApexForgingRecipe recipe) {
            buf.writeEnum(recipe.school());
            recipe.input().toNetwork(buf);
            buf.writeItem(recipe.result());
        }
    }
}
