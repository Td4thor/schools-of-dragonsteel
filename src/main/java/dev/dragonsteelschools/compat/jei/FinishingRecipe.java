package dev.dragonsteelschools.compat.jei;

import dev.dragonsteelschools.school.SchoolSteel;
import io.redspace.ironsspellbooks.api.spells.AbstractSpell;
import net.minecraft.world.item.ItemStack;

/**
 * One way to finish a school's tempered steel at a dragon forge: one spell, for JEI's Dragonsteel Finishing pages.
 *
 * @param minLevel the lowest level at which the spell is of Legendary rarity (1 for an Apex spell, which works at any)
 * @param apex     whether the spell is on the config's Apex list (it works under either finishing rule)
 */
public record FinishingRecipe(SchoolSteel school, ItemStack tempered, ItemStack ingot, AbstractSpell spell, int minLevel, boolean apex) {
}
