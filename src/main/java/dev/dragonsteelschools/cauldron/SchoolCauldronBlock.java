package dev.dragonsteelschools.cauldron;

import dev.dragonsteelschools.school.SchoolSteel;
import net.minecraft.core.BlockPos;
import net.minecraft.core.cauldron.CauldronInteraction;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.LayeredCauldronBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.Fluid;
import org.jetbrains.annotations.Nullable;
import org.joml.Vector3f;

import java.util.Map;

/**
 * A three-level cauldron of dragon's breath (school == null) or of one school's dragon blood. Neither fills from
 * rain or dripstone, and neither puts out burning entities the way water does.
 */
public class SchoolCauldronBlock extends LayeredCauldronBlock {
    @Nullable
    private final SchoolSteel school;

    public SchoolCauldronBlock(@Nullable SchoolSteel school, Properties properties, Map<Item, CauldronInteraction> interactions) {
        super(properties, precipitation -> false, interactions);
        this.school = school;
    }

    @Nullable
    public SchoolSteel school() {
        return school;
    }

    @Override
    public void entityInside(BlockState state, Level level, BlockPos pos, Entity entity) {
        // Not water: nothing is extinguished and no level is used up.
    }

    @Override
    protected boolean canReceiveStalactiteDrip(Fluid fluid) {
        return false;
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        double surface = pos.getY() + (6.0 + 3.0 * state.getValue(LEVEL)) / 16.0;
        double x = pos.getX() + 0.25 + random.nextDouble() * 0.5;
        double z = pos.getZ() + 0.25 + random.nextDouble() * 0.5;
        if (school == null) {
            if (random.nextInt(3) == 0) {
                level.addParticle(ParticleTypes.DRAGON_BREATH, x, surface, z, 0.0, 0.01, 0.0);
            }
        } else if (school == SchoolSteel.HOLY) {
            if (random.nextInt(2) == 0) {
                level.addParticle(new DustParticleOptions(new Vector3f(1.0F, 0.86F, 0.45F), 0.8F), x, surface, z, 0.0, 0.02, 0.0);
            }
            if (random.nextInt(6) == 0) {
                level.addParticle(ParticleTypes.END_ROD, x, surface, z, 0.0, 0.015, 0.0);
            }
        } else {
            if (random.nextInt(2) == 0) {
                level.addParticle(ParticleTypes.REVERSE_PORTAL, x, surface, z, 0.0, 0.02, 0.0);
            }
        }
    }
}
