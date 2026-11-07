package dev.dragonsteelschools.cauldron;

import dev.dragonsteelschools.registry.ModBlocks;
import dev.dragonsteelschools.school.SchoolSteel;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.block.LayeredCauldronBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.gameevent.GameEvent;
import org.joml.Vector3f;

/** Any spell of a school, cast at a cauldron of dragon's breath, turns it into that school's dragon blood. */
public final class SchoolCauldrons {
    private SchoolCauldrons() {
    }

    /** @return true if the target was a breath cauldron (whether or not it could be changed). */
    public static boolean tryAttune(ServerPlayer caster, ServerLevel level, BlockPos pos, SchoolSteel school) {
        BlockState state = level.getBlockState(pos);
        if (!state.is(ModBlocks.BREATH_CAULDRON.get())) {
            return false;
        }
        if (!level.mayInteract(caster, pos)) {
            return true;
        }
        int fill = state.getValue(LayeredCauldronBlock.LEVEL);
        level.setBlockAndUpdate(pos, ModBlocks.BLOOD_CAULDRON.get(school).get().defaultBlockState()
                .setValue(LayeredCauldronBlock.LEVEL, fill));
        level.gameEvent(caster, GameEvent.BLOCK_CHANGE, pos);
        double x = pos.getX() + 0.5;
        double y = pos.getY() + 0.9;
        double z = pos.getZ() + 0.5;
        level.sendParticles(dust(school, 1.2F), x, y, z, 30, 0.3, 0.3, 0.3, 0.02);
        level.sendParticles(school.particle(), x, y, z, 24, 0.25, 0.4, 0.25, 0.04);
        level.sendParticles(ParticleTypes.DRAGON_BREATH, x, y, z, 12, 0.3, 0.2, 0.3, 0.01);
        level.playSound(null, pos, SoundEvents.BREWING_STAND_BREW, SoundSource.BLOCKS, 1.0F, 1.0F);
        level.playSound(null, pos, school.forgeSound(), SoundSource.BLOCKS, 0.6F, 1.4F);
        caster.displayClientMessage(Component.translatable("message.dragonsteel_schools.cauldron.attuned", school.displayName()), true);
        return true;
    }

    /** Dust in the school's colour. */
    public static DustParticleOptions dust(SchoolSteel school, float size) {
        int rgb = school.primaryColor();
        return new DustParticleOptions(new Vector3f(((rgb >> 16) & 255) / 255F, ((rgb >> 8) & 255) / 255F, (rgb & 255) / 255F), size);
    }
}
