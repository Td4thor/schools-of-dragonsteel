package dev.dragonsteelschools.gametest;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraftforge.registries.ForgeRegistries;

import java.lang.reflect.Field;
import java.lang.reflect.Method;

/**
 * Builds a real Ice and Fire dragon forge from registry names and feeds it breath through the input block's own
 * {@code onHitWithFlame}, the method Ice and Fire's dragon-breath code calls. Tests only; nothing is compiled
 * against Ice and Fire.
 */
final class ForgeFixtures {
    private ForgeFixtures() {
    }

    static Block block(String path) {
        Block block = ForgeRegistries.BLOCKS.getValue(new ResourceLocation("iceandfire", path));
        if (block == null || block == Blocks.AIR) {
            throw new IllegalStateException("Ice and Fire block missing: " + path);
        }
        return block;
    }

    /** The 3x3x3 multiblock: bone corners top and bottom, bricks elsewhere, the input on one side of the core. */
    static void build(GameTestHelper helper, BlockPos core, String element, Direction inputSide) {
        Block brick = block("dragonforge_" + element + "_brick");
        Block bone = block("dragon_bone_block");
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                boolean corner = dx != 0 && dz != 0;
                helper.setBlock(core.offset(dx, -1, dz), corner ? bone : brick);
                helper.setBlock(core.offset(dx, 1, dz), corner ? bone : brick);
                if (dx != 0 || dz != 0) {
                    helper.setBlock(core.offset(dx, 0, dz), brick);
                }
            }
        }
        helper.setBlock(core.relative(inputSide), block("dragonforge_" + element + "_input"));
        helper.setBlock(core, block("dragonforge_" + element + "_core_disabled"));
    }

    static void breathe(GameTestHelper helper, BlockPos input) {
        BlockEntity be = helper.getBlockEntity(input);
        try {
            Method hit = be.getClass().getMethod("onHitWithFlame");
            hit.invoke(be);
        } catch (ReflectiveOperationException failure) {
            throw new IllegalStateException("Could not breathe into " + be, failure);
        }
    }

    static boolean assembled(BlockEntity core) {
        try {
            return (Boolean) core.getClass().getMethod("assembled").invoke(core);
        } catch (ReflectiveOperationException failure) {
            throw new IllegalStateException("No assembled() on " + core, failure);
        }
    }

    static int flameTimer(BlockEntity core) {
        try {
            Field field = core.getClass().getField("lastDragonFlameTimer");
            return field.getInt(core);
        } catch (ReflectiveOperationException failure) {
            throw new IllegalStateException("No flame timer on " + core, failure);
        }
    }
}
