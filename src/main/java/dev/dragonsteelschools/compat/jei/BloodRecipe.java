package dev.dragonsteelschools.compat.jei;

import dev.dragonsteelschools.school.SchoolSteel;
import io.redspace.ironsspellbooks.api.spells.AbstractSpell;
import net.minecraft.world.item.ItemStack;

import java.util.List;

/** How a school's dragon blood is brewed in a cauldron, for JEI's School Dragon Blood page. */
public record BloodRecipe(SchoolSteel school, ItemStack blood, List<AbstractSpell> spells) {
}
