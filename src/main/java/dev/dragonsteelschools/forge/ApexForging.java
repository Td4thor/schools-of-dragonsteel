package dev.dragonsteelschools.forge;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.registry.ModRegistries;
import dev.dragonsteelschools.school.SchoolSteel;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.Container;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.gameevent.GameEvent;
import org.joml.Vector3f;

import java.util.List;
import java.util.Optional;

/**
 * A finishing cast landing on a dragon forge (see {@link FinishingRule}: a Legendary cast of the school or an Apex
 * spell). The dragon has already done its part: its breath tempered iron and school blood into tempered steel (an
 * ordinary Ice and Fire forge recipe). The cast finishes every piece of its own school's tempered steel in the forge at
 * once, up to a full stack, turning it into dragonsteel where it lies.
 */
public final class ApexForging {
    public enum Outcome { NOT_A_FORGE, PROTECTED, NOTHING_TEMPERED, TOO_MUCH, FORGED }

    private static final int[] SLOTS = {DragonForges.SLOT_OUTPUT, DragonForges.SLOT_INPUT};

    private ApexForging() {
    }

    public static Outcome tryForge(ServerPlayer caster, ServerLevel level, BlockPos hit, SchoolSteel school) {
        Optional<BlockPos> found = DragonForges.findCore(level, hit);
        if (found.isEmpty()) {
            return Outcome.NOT_A_FORGE;
        }
        BlockPos core = found.get();
        if (!level.mayInteract(caster, core)) {
            return Outcome.PROTECTED;
        }
        Container forge = DragonForges.container(level, core);
        if (forge == null) {
            return Outcome.NOT_A_FORGE;
        }
        List<ApexForgingRecipe> recipes = level.getRecipeManager().getAllRecipesFor(ModRegistries.APEX_FORGING.get()).stream()
                .filter(r -> r.school() == school)
                .toList();
        int budget = ForgeBatchMath.MAX_PER_CAST;
        int made = 0;
        boolean anyTempered = false;
        ItemStack lastResult = ItemStack.EMPTY;
        for (int slot : SLOTS) {
            ItemStack stack = forge.getItem(slot);
            Optional<ApexForgingRecipe> recipe = recipes.stream().filter(r -> r.accepts(stack)).findFirst();
            if (recipe.isEmpty()) {
                continue;
            }
            anyTempered = true;
            ItemStack result = recipe.get().assemble(forge, level.registryAccess());
            int units = ForgeBatchMath.finishSlot(stack.getCount(), budget, result.getCount(), result.getMaxStackSize());
            if (units <= 0) {
                continue;
            }
            forge.setItem(slot, result.copyWithCount(units * result.getCount()));
            budget -= units;
            made += units * result.getCount();
            lastResult = result;
        }
        if (made == 0) {
            caster.displayClientMessage(Component.translatable(anyTempered
                    ? "message.dragonsteel_schools.forge.too_much" : "message.dragonsteel_schools.forge.nothing",
                    school.displayName(), ForgeBatchMath.MAX_PER_CAST), true);
            return anyTempered ? Outcome.TOO_MUCH : Outcome.NOTHING_TEMPERED;
        }
        forge.setChanged();
        celebrate(level, core, school);
        level.gameEvent(caster, GameEvent.BLOCK_CHANGE, core);
        caster.displayClientMessage(Component.translatable("message.dragonsteel_schools.forge.done", made, lastResult.getHoverName()), true);
        DragonsteelSchools.LOG.debug("{} finished {} x {} at {} with {}", caster.getGameProfile().getName(), made, lastResult, core, school);
        return Outcome.FORGED;
    }

    /** Whether the forge at or around {@code hit} holds tempered steel this school can finish. */
    public static boolean holdsTempered(ServerLevel level, BlockPos hit, SchoolSteel school) {
        Optional<BlockPos> core = DragonForges.findCore(level, hit);
        Container forge = core.map(c -> DragonForges.container(level, c)).orElse(null);
        if (forge == null) {
            return false;
        }
        List<ApexForgingRecipe> recipes = level.getRecipeManager().getAllRecipesFor(ModRegistries.APEX_FORGING.get()).stream()
                .filter(r -> r.school() == school)
                .toList();
        for (int slot : SLOTS) {
            ItemStack stack = forge.getItem(slot);
            if (!stack.isEmpty() && recipes.stream().anyMatch(r -> r.accepts(stack))) {
                return true;
            }
        }
        return false;
    }

    private static void celebrate(ServerLevel level, BlockPos core, SchoolSteel school) {
        double x = core.getX() + 0.5;
        double y = core.getY() + 0.5;
        double z = core.getZ() + 0.5;
        int rgb = school.primaryColor();
        ParticleOptions dust = new DustParticleOptions(new Vector3f(((rgb >> 16) & 255) / 255F, ((rgb >> 8) & 255) / 255F, (rgb & 255) / 255F), 1.6F);
        level.sendParticles(dust, x, y + 1.0, z, 80, 1.2, 1.2, 1.2, 0.02);
        level.sendParticles(school.particle(), x, y + 1.0, z, 60, 0.8, 1.4, 0.8, 0.08);
        level.playSound(null, core, school.forgeSound(), SoundSource.BLOCKS, 1.4F, 1.0F);
        level.playSound(null, core, SoundEvents.ANVIL_USE, SoundSource.BLOCKS, 1.0F, 0.6F);
    }
}
