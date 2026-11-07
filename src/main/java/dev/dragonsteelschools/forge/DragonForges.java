package dev.dragonsteelschools.forge;

import dev.dragonsteelschools.DragonsteelSchools;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.Container;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import org.jetbrains.annotations.Nullable;

import java.util.Optional;

/**
 * THE ONLY JAVA THAT KNOWS WHAT A DRAGON FORGE IS. Porting to Ice and Fire 2 starts here and in the data files.
 *
 * <p>Nothing is compiled against Ice and Fire. A forge is found through two block tags
 * ({@code dragonsteel_schools:dragon_forge_cores} and {@code :dragon_forge_parts}) and its slots are used through
 * Minecraft's own {@link Container} interface (Ice and Fire 2.1.13: 0 input, 1 blood, 2 output). The dragon's part
 * of the work, tempering iron with school blood, is an ordinary Ice and Fire forge recipe in
 * {@code data/dragonsteel_schools/recipes/iceandfire/}, so Ice and Fire itself decides when a dragon is breathing.
 */
public final class DragonForges {
    public static final TagKey<Block> CORES = BlockTags.create(new ResourceLocation(DragonsteelSchools.MODID, "dragon_forge_cores"));
    public static final TagKey<Block> PARTS = BlockTags.create(new ResourceLocation(DragonsteelSchools.MODID, "dragon_forge_parts"));

    public static final int SLOT_INPUT = 0;
    public static final int SLOT_BLOOD = 1;
    public static final int SLOT_OUTPUT = 2;

    private DragonForges() {
    }

    /** The core of the forge that {@code hit} belongs to. Every part of the 3x3x3 forge touches its core. */
    public static Optional<BlockPos> findCore(Level level, BlockPos hit) {
        if (isCore(level, hit)) {
            return Optional.of(hit.immutable());
        }
        if (!level.getBlockState(hit).is(PARTS)) {
            return Optional.empty();
        }
        BlockPos best = null;
        double bestDistance = Double.MAX_VALUE;
        for (BlockPos candidate : BlockPos.betweenClosed(hit.offset(-1, -1, -1), hit.offset(1, 1, 1))) {
            if (isCore(level, candidate)) {
                double distance = candidate.distSqr(hit);
                if (distance < bestDistance) {
                    bestDistance = distance;
                    best = candidate.immutable();
                }
            }
        }
        return Optional.ofNullable(best);
    }

    private static boolean isCore(Level level, BlockPos pos) {
        return level.getBlockState(pos).is(CORES) && container(level, pos) != null;
    }

    @Nullable
    public static Container container(Level level, BlockPos core) {
        return level.getBlockEntity(core) instanceof Container container && container.getContainerSize() > SLOT_OUTPUT
                ? container : null;
    }
}
