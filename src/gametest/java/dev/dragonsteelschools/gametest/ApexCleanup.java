package dev.dragonsteelschools.gametest;

import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.entity.Entity;
import net.minecraftforge.registries.ForgeRegistries;

import java.util.ArrayList;
import java.util.List;

/**
 * Apex Arcana's spells leave domains behind (an eye in the sky, an arena, a tree) that outlive the test that cast them.
 * GameTest batches reuse the same spot, so a leftover domain eats the next test's Apex cast or stops its caster
 * casting at all. Every Apex test clears them before it starts and after it ends.
 */
final class ApexCleanup {
    private ApexCleanup() {
    }

    static int clear(GameTestHelper helper) {
        List<Entity> doomed = new ArrayList<>();
        for (Entity entity : helper.getLevel().getAllEntities()) {
            var key = ForgeRegistries.ENTITY_TYPES.getKey(entity.getType());
            if (key != null && key.getNamespace().equals("grandsigil")) {
                doomed.add(entity);
            }
        }
        doomed.forEach(Entity::discard);
        return doomed.size();
    }
}
